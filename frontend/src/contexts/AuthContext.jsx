import { createContext, useContext, useState } from "react";
import { authLogin, authSignup } from "@/lib/api";

const SESSION_KEY = "forensiq_session";
const TOKEN_KEY = "forensiq_token";

function loadSession() {
  try {
    const stored = localStorage.getItem(SESSION_KEY);
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
}

function saveSession(user, token) {
  try {
    if (user) {
      localStorage.setItem(SESSION_KEY, JSON.stringify(user));
      if (token) localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(SESSION_KEY);
      localStorage.removeItem(TOKEN_KEY);
    }
  } catch { /* ignore */ }
}

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => loadSession());

  const login = async (email, password) => {
    try {
      const res = await authLogin({ email, password });
      if (res && res.user) {
        setUser(res.user);
        saveSession(res.user, res.token);
        return true;
      }
      return false;
    } catch (err) {
      // Rethrow so LoginPage can display the error
      throw err;
    }
  };

  const signup = async ({ name, email, password, role, department }) => {
    try {
      const res = await authSignup({ name, email, password, role, department });
      if (res && res.user) {
        setUser(res.user);
        saveSession(res.user, res.token);
        return true;
      }
      return false;
    } catch (err) {
      throw err;
    }
  };

  const logout = () => {
    setUser(null);
    saveSession(null);
  };

  return <AuthContext.Provider value={{ user, login, signup, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
