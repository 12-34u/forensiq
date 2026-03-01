import { createContext, useContext, useState, useCallback, useRef } from "react";
import {
  createConversation as apiCreate,
  listConversations as apiList,
  getConversation as apiGet,
  appendMessage as apiAppend,
  renameConversation as apiRename,
  deleteConversation as apiDelete,
} from "@/lib/api";

const ChatContext = createContext(null);

/**
 * Manages per-user conversation state:
 * - conversations: list of conversation summaries (id, title, timestamps)
 * - activeConversation: the full conversation currently open (with messages)
 * - CRUD helpers that sync with the MongoDB backend
 */
export function ChatProvider({ children }) {
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [loading, setLoading] = useState(false);

  // Keep a ref that always points to the latest active conversation
  // so addMessage never suffers a stale closure.
  const activeConvRef = useRef(activeConversation);
  activeConvRef.current = activeConversation;

  /** Fetch the conversation list from the backend. */
  const refreshList = useCallback(async () => {
    try {
      const list = await apiList();
      setConversations(list);
    } catch {
      // silently fail — user may not be logged in yet
    }
  }, []);

  /** Create a new conversation and make it active. */
  const startConversation = useCallback(async (title) => {
    setLoading(true);
    try {
      const conv = await apiCreate(title || "New Conversation");
      setActiveConversation(conv);
      // Prepend to list
      setConversations(prev => [{
        id: conv.id,
        user_id: conv.user_id,
        title: conv.title,
        created_at: conv.created_at,
        updated_at: conv.updated_at,
        message_count: 0,
      }, ...prev]);
      return conv;
    } finally {
      setLoading(false);
    }
  }, []);

  /** Open an existing conversation (fetches full messages). */
  const openConversation = useCallback(async (conversationId) => {
    setLoading(true);
    try {
      const conv = await apiGet(conversationId);
      setActiveConversation(conv);
      return conv;
    } finally {
      setLoading(false);
    }
  }, []);

  /** Append a message to the active conversation (both local state + DB).
   *  Pass an explicit `conversationId` to avoid stale-closure issues
   *  (e.g. first message right after startConversation).
   */
  const addMessage = useCallback(async (message, conversationId) => {
    const convId = conversationId || activeConvRef.current?.id;
    if (!convId) return;
    // Optimistic local update
    setActiveConversation(prev => {
      if (!prev || prev.id !== convId) return prev;
      return { ...prev, messages: [...(prev?.messages || []), message] };
    });
    // Persist to backend
    try {
      await apiAppend(convId, message);
    } catch (err) {
      console.error("Failed to persist message:", err);
    }
  }, []);

  /** Auto-title a conversation from the first user message. */
  const autoTitle = useCallback(async (conversationId, firstMessage) => {
    const title = firstMessage.length > 50
      ? firstMessage.slice(0, 50) + "…"
      : firstMessage;
    try {
      await apiRename(conversationId, title);
      setActiveConversation(prev =>
        prev?.id === conversationId ? { ...prev, title } : prev
      );
      setConversations(prev =>
        prev.map(c => c.id === conversationId ? { ...c, title } : c)
      );
    } catch {
      // non-critical
    }
  }, []);

  /** Rename a conversation. */
  const rename = useCallback(async (conversationId, title) => {
    await apiRename(conversationId, title);
    setConversations(prev =>
      prev.map(c => c.id === conversationId ? { ...c, title } : c)
    );
    setActiveConversation(prev =>
      prev?.id === conversationId ? { ...prev, title } : prev
    );
  }, []);

  /** Delete a conversation. */
  const remove = useCallback(async (conversationId) => {
    await apiDelete(conversationId);
    setConversations(prev => prev.filter(c => c.id !== conversationId));
    if (activeConversation?.id === conversationId) {
      setActiveConversation(null);
    }
  }, [activeConversation]);

  /** Close the active conversation (go back to empty state). */
  const closeConversation = useCallback(() => {
    setActiveConversation(null);
  }, []);

  return (
    <ChatContext.Provider
      value={{
        conversations,
        activeConversation,
        loading,
        refreshList,
        startConversation,
        openConversation,
        addMessage,
        autoTitle,
        rename,
        remove,
        closeConversation,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be used within ChatProvider");
  return ctx;
}
