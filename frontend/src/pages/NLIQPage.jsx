import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2, Plus, MessageSquare, Trash2, Pencil, X, Check, ChevronLeft } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { query as apiQuery } from "@/lib/api";
import { useCase } from "@/contexts/CaseContext";
import { useChat } from "@/contexts/ChatContext";

const sourceColors = {
  WhatsApp: "bg-success/15 text-success",
  Telegram: "bg-primary/15 text-primary",
  SMS: "bg-accent/15 text-accent",
  Signal: "bg-chart-5/15 text-chart-5",
  vector: "bg-primary/15 text-primary",
  graph: "bg-accent/15 text-accent",
};

const suggestedQueries = [
  "Find mentions of international bank transfers or crypto wallets",
  "Show communications with foreign numbers",
  "List all messages with anti-forensic intent",
  "Who are the key suspects and how are they connected?",
  "Show timeline of suspicious activity on December 10",
];

export default function NLIQPage() {
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [expandedCitation, setExpandedCitation] = useState(null);
  const [showSidebar, setShowSidebar] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState("");
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);
  const { activeProject } = useCase();
  const {
    conversations,
    activeConversation,
    loading: chatLoading,
    refreshList,
    startConversation,
    openConversation,
    addMessage,
    autoTitle,
    rename,
    remove,
    closeConversation,
  } = useChat();

  const messages = activeConversation?.messages || [];

  // Load conversation list on mount
  useEffect(() => {
    refreshList();
  }, [refreshList]);

  // Auto-scroll on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  const sendMessage = async (text) => {
    if (!text.trim() || isThinking) return;

    let convId = activeConversation?.id;

    // Auto-create a conversation if none is active
    if (!convId) {
      const conv = await startConversation("New Conversation");
      convId = conv.id;
    }

    const userMsg = {
      id: `u-${Date.now()}`,
      role: "user",
      content: text.trim(),
      timestamp: new Date().toISOString(),
    };

    // Persist user message (pass convId explicitly to avoid stale closure)
    await addMessage(userMsg, convId);
    setInput("");
    setIsThinking(true);

    // Auto-title from first message
    if (messages.length === 0) {
      autoTitle(convId, text.trim());
    }

    try {
      const result = await apiQuery(text.trim());

      const vectorCitations = (result.vector_hits || []).map((hit, i) => ({
        id: `v-${i}`,
        type: "vector",
        title: hit.title || `Vector Hit #${i + 1}`,
        body: hit.body || hit.text || "",
        score: hit.score ?? hit.similarity ?? 0,
        artifact_type: hit.artifact_type || "",
        source_section: hit.source_section || "",
        page_id: hit.page_id || "",
      }));

      const graphCitations = (result.graph_context || []).map((ctx, i) => ({
        id: `g-${i}`,
        type: "graph",
        title: ctx.title || ctx.name || `Graph Entity #${i + 1}`,
        body: ctx.body || ctx.text || JSON.stringify(ctx.properties || ctx, null, 2),
        label: ctx.label || ctx.type || "",
        page_id: ctx.page_id || "",
      }));

      const allCitations = [...vectorCitations, ...graphCitations];

      const assistantMsg = {
        id: `a-${Date.now()}`,
        role: "assistant",
        content: result.answer,
        citations: allCitations,
        source: result.source,
        cacheKey: result.cache_key,
        timestamp: new Date().toISOString(),
      };
      await addMessage(assistantMsg, convId);
    } catch (err) {
      const errorMsg = {
        id: `e-${Date.now()}`,
        role: "assistant",
        content: `**Error:** ${err.message}\n\nMake sure the ForensIQ backend is running and data has been ingested.`,
        citations: [],
        timestamp: new Date().toISOString(),
      };
      await addMessage(errorMsg, convId);
    } finally {
      setIsThinking(false);
    }
  };

  const handleNewChat = async () => {
    await startConversation("New Conversation");
  };

  const handleSelectConv = async (convId) => {
    if (convId === activeConversation?.id) return;
    await openConversation(convId);
  };

  const handleDelete = async (e, convId) => {
    e.stopPropagation();
    await remove(convId);
  };

  const handleRenameStart = (e, conv) => {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditTitle(conv.title);
  };

  const handleRenameSubmit = async (e, convId) => {
    e.stopPropagation();
    if (editTitle.trim()) {
      await rename(convId, editTitle.trim());
    }
    setEditingId(null);
  };

  return (
    <div className="flex h-full">
      {/* ── Conversation Sidebar ── */}
      <AnimatePresence>
        {showSidebar && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 260, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="flex flex-col border-r border-border bg-sidebar overflow-hidden"
          >
            {/* Sidebar Header */}
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Chat History</span>
              <button
                onClick={handleNewChat}
                className="flex items-center gap-1.5 rounded-lg bg-primary/10 px-2.5 py-1.5 text-[11px] font-medium text-primary transition-colors hover:bg-primary/20"
              >
                <Plus className="h-3.5 w-3.5" />
                New
              </button>
            </div>

            {/* Conversation List */}
            <div className="flex-1 overflow-y-auto scrollbar-thin px-2 py-2 space-y-0.5">
              {conversations.length === 0 && (
                <p className="px-3 py-6 text-center text-[11px] text-muted-foreground">
                  No conversations yet.<br />Start one with the button above.
                </p>
              )}
              {conversations.map(conv => {
                const isActive = conv.id === activeConversation?.id;
                const isEditing = editingId === conv.id;
                return (
                  <div
                    key={conv.id}
                    onClick={() => handleSelectConv(conv.id)}
                    className={`group flex items-center gap-2 rounded-lg px-3 py-2.5 cursor-pointer transition-colors ${
                      isActive
                        ? "bg-primary/10 text-foreground"
                        : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                    }`}
                  >
                    <MessageSquare className="h-3.5 w-3.5 flex-shrink-0" />
                    {isEditing ? (
                      <div className="flex flex-1 items-center gap-1" onClick={e => e.stopPropagation()}>
                        <input
                          value={editTitle}
                          onChange={e => setEditTitle(e.target.value)}
                          onKeyDown={e => e.key === "Enter" && handleRenameSubmit(e, conv.id)}
                          className="flex-1 rounded border border-border bg-background px-1.5 py-0.5 text-[11px] text-foreground outline-none focus:border-primary"
                          autoFocus
                        />
                        <button onClick={e => handleRenameSubmit(e, conv.id)} className="text-success hover:text-success/80">
                          <Check className="h-3 w-3" />
                        </button>
                        <button onClick={() => setEditingId(null)} className="text-muted-foreground hover:text-foreground">
                          <X className="h-3 w-3" />
                        </button>
                      </div>
                    ) : (
                      <>
                        <div className="flex-1 min-w-0">
                          <p className="truncate text-[11px] font-medium">{conv.title}</p>
                          <p className="text-[9px] font-mono text-muted-foreground/60">
                            {conv.message_count || 0} msg{(conv.message_count || 0) !== 1 ? "s" : ""}
                          </p>
                        </div>
                        <div className="hidden group-hover:flex items-center gap-0.5">
                          <button
                            onClick={e => handleRenameStart(e, conv)}
                            className="rounded p-1 hover:bg-secondary"
                            title="Rename"
                          >
                            <Pencil className="h-3 w-3" />
                          </button>
                          <button
                            onClick={e => handleDelete(e, conv.id)}
                            className="rounded p-1 hover:bg-destructive/10 text-destructive"
                            title="Delete"
                          >
                            <Trash2 className="h-3 w-3" />
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* ── Main Chat Area ── */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center gap-3 border-b border-border px-6 py-4">
          <button
            onClick={() => setShowSidebar(v => !v)}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
            title={showSidebar ? "Hide history" : "Show history"}
          >
            {showSidebar ? <ChevronLeft className="h-4 w-4" /> : <MessageSquare className="h-4 w-4" />}
          </button>
          <div>
            <h2 className="text-lg font-bold text-foreground">
              {activeConversation ? activeConversation.title : "NLIQ — Investigative Chat"}
            </h2>
            <p className="text-xs text-muted-foreground">
              {activeConversation
                ? `${messages.length} messages`
                : "Ask questions in natural language. AI retrieves evidence with source citations."}
            </p>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto scrollbar-thin px-6 py-4">
          {messages.length === 0 && !isThinking && (
            <div className="flex h-full flex-col items-center justify-center gap-6">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
                <Bot className="h-8 w-8 text-primary" />
              </div>
              <div className="text-center">
                <p className="text-sm font-semibold text-foreground">Ask me anything about the case evidence</p>
                <p className="mt-1 text-xs text-muted-foreground">I understand natural language and search across all ingested device data</p>
              </div>
              <div className="flex flex-wrap justify-center gap-2 max-w-lg">
                {suggestedQueries.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(q)}
                    className="rounded-lg border border-border bg-card px-3 py-2 text-xs text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-4">
            <AnimatePresence>
              {messages.map(msg => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
                >
                  {msg.role === "assistant" && (
                    <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg bg-primary/10 mt-0.5">
                      <Bot className="h-4 w-4 text-primary" />
                    </div>
                  )}

                  <div className={`max-w-[85%] ${msg.role === "user" ? "order-first" : ""}`}>
                    <div className={`rounded-xl px-4 py-3 text-sm ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground rounded-br-sm"
                        : "bg-card border border-border rounded-bl-sm"
                    }`}>
                      {msg.role === "assistant" ? (
                        <div className="space-y-2 text-foreground">
                          {msg.content.split("\n").map((line, i) => {
                            if (line.startsWith("### ")) return <h3 key={i} className="mt-3 mb-1 text-xs font-bold uppercase tracking-wider text-muted-foreground">{line.replace("### ", "")}</h3>;
                            if (line.startsWith("## ")) return <h2 key={i} className="mt-3 mb-1 text-sm font-bold text-foreground">{line.replace("## ", "")}</h2>;
                            if (line.startsWith("- **")) {
                              const parts = line.match(/- \*\*(.+?)\*\*:?\s*(.*)/);
                              if (parts) return <div key={i} className="flex items-center gap-2 text-xs"><span className="rounded border border-primary/30 bg-primary/10 px-1.5 py-0.5 text-[10px] font-bold text-primary">{parts[1]}</span><span className="text-muted-foreground">{parts[2]}</span></div>;
                            }
                            if (line.startsWith("- ")) {
                              return <div key={i} className="flex items-start gap-2 text-xs ml-1"><span className="text-primary mt-0.5">•</span><span className="text-muted-foreground">{line.slice(2)}</span></div>;
                            }
                            const rendered = line.split(/(\*\*.+?\*\*)/).map((seg, j) =>
                              seg.startsWith("**") && seg.endsWith("**")
                                ? <strong key={j} className="font-semibold text-foreground">{seg.slice(2, -2)}</strong>
                                : <span key={j}>{seg}</span>
                            );
                            return line.trim() ? <p key={i} className="text-xs leading-relaxed text-muted-foreground">{rendered}</p> : null;
                          })}
                        </div>
                      ) : (
                        <p>{msg.content}</p>
                      )}
                    </div>

                    {/* Citations */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-2 space-y-1.5">
                        {msg.citations.map((cite, idx) => (
                          <div key={cite.id} className="rounded-lg border border-border bg-card overflow-hidden">
                            <button
                              onClick={() => setExpandedCitation(expandedCitation === cite.id ? null : cite.id)}
                              className="flex w-full items-center gap-3 px-3 py-2 text-left hover:bg-muted/50 transition-colors"
                            >
                              <span className="flex h-5 w-5 items-center justify-center rounded bg-primary/10 text-[10px] font-bold text-primary font-mono">{idx + 1}</span>
                              <span className={`rounded px-1.5 py-0.5 text-[9px] font-bold ${sourceColors[cite.type] || "bg-muted text-muted-foreground"}`}>
                                {cite.type === "vector" ? "VECTOR" : "GRAPH"}
                              </span>
                              {cite.artifact_type && (
                                <span className="rounded bg-secondary px-1.5 py-0.5 text-[9px] font-mono text-secondary-foreground">
                                  {cite.artifact_type}
                                </span>
                              )}
                              {cite.label && (
                                <span className="rounded bg-accent/15 px-1.5 py-0.5 text-[9px] font-mono text-accent">
                                  {cite.label}
                                </span>
                              )}
                              <span className="flex-1 truncate text-[11px] text-muted-foreground">{cite.title}</span>
                              {cite.score != null && (
                                <span className="text-[10px] font-mono text-primary">{Math.round(cite.score * 100)}%</span>
                              )}
                            </button>

                            <AnimatePresence>
                              {expandedCitation === cite.id && (
                                <motion.div
                                  initial={{ height: 0 }}
                                  animate={{ height: "auto" }}
                                  exit={{ height: 0 }}
                                  className="overflow-hidden"
                                >
                                  <div className="border-t border-border bg-muted/30 px-3 py-2.5 space-y-2">
                                    <p className="text-xs text-foreground leading-relaxed whitespace-pre-wrap">{cite.body}</p>
                                    <div className="flex items-center gap-3 text-[10px] font-mono text-muted-foreground">
                                      {cite.source_section && <span>{cite.source_section}</span>}
                                      {cite.page_id && <span>Page: {cite.page_id.slice(0, 8)}…</span>}
                                    </div>
                                  </div>
                                </motion.div>
                              )}
                            </AnimatePresence>
                          </div>
                        ))}
                      </div>
                    )}

                    <p className="mt-1 text-[9px] font-mono text-muted-foreground/50 px-1">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </p>
                  </div>

                  {msg.role === "user" && (
                    <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg bg-accent/10 mt-0.5">
                      <User className="h-4 w-4 text-accent" />
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            {isThinking && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
                <div className="rounded-xl border border-border bg-card px-4 py-3 rounded-bl-sm">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
                    Searching across device data…
                  </div>
                </div>
              </motion.div>
            )}
            <div ref={chatEndRef} />
          </div>
        </div>

        {/* Input */}
        <div className="border-t border-border px-6 py-4">
          <div className="flex gap-3">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && sendMessage(input)}
              placeholder="Ask: 'Show me all crypto wallet references' or 'Who communicated with Dubai numbers?'"
              className="w-full rounded-xl border border-border bg-card py-3 pl-4 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || isThinking}
              className="flex h-[46px] w-[46px] items-center justify-center rounded-xl bg-primary text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-40"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
