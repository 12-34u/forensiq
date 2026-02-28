import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { listProjects, getStats } from "@/lib/api";

const CaseContext = createContext(null);

/**
 * Provides shared state across the dashboard:
 * - projects: list of ingested devices / projects from Neo4j
 * - activeProject: currently selected project (set after upload or click)
 * - stats: backend system stats (FAISS vectors, Neo4j counts, extractions)
 * - refresh(): re-fetch projects + stats from backend
 * - lastIngestResult: result from the most recent ingest (for passing between pages)
 */
export function CaseProvider({ children }) {
  const [projects, setProjects] = useState([]);
  const [activeProject, setActiveProject] = useState(null);
  const [stats, setStats] = useState(null);
  const [lastIngestResult, setLastIngestResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [projectList, sysStats] = await Promise.all([
        listProjects().catch(() => []),
        getStats().catch(() => null),
      ]);
      setProjects(projectList);
      setStats(sysStats);
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-fetch on mount
  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <CaseContext.Provider
      value={{
        projects,
        activeProject,
        setActiveProject,
        stats,
        lastIngestResult,
        setLastIngestResult,
        loading,
        refresh,
      }}
    >
      {children}
    </CaseContext.Provider>
  );
}

export function useCase() {
  const ctx = useContext(CaseContext);
  if (!ctx) throw new Error("useCase must be used within CaseProvider");
  return ctx;
}
