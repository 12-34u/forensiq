import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, Shield, FileText, CheckCircle, Loader2, AlertCircle, LogOut, Sun, Moon, FolderOpen, Clock, AlertTriangle, Users, Database, Cpu } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/hooks/use-theme";
import { useCase } from "@/contexts/CaseContext";
import { ingestUpload } from "@/lib/api";

const processingSteps = [
  "Uploading file to server…",
  "Extracting device metadata…",
  "Parsing chat databases (WhatsApp, Telegram, Signal, SMS)…",
  "Indexing call logs & contacts…",
  "Building vector embeddings for semantic search…",
  "Constructing entity relationship graph…",
  "Finalizing evidence index…",
];

export default function HomePage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { projects, stats, loading: caseLoading, refresh, setActiveProject, setLastIngestResult } = useCase();

  const [uploadState, setUploadState] = useState("idle");    // idle | uploading | processing | done | error
  const [fileName, setFileName] = useState("");
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [uploadError, setUploadError] = useState("");

  const handleIngest = useCallback(async (file) => {
    setFileName(file.name);
    setUploadState("uploading");
    setProgress(0);
    setUploadError("");

    // Simulate upload progress while actual upload happens
    let uploadProgress = 0;
    const uploadInterval = setInterval(() => {
      uploadProgress += Math.random() * 8 + 2;
      if (uploadProgress >= 60) {
        clearInterval(uploadInterval);
        setProgress(60);
      } else {
        setProgress(Math.min(uploadProgress, 60));
      }
    }, 300);

    try {
      setCurrentStep(0);
      setUploadState("processing");

      // Actual API call to backend
      const result = await ingestUpload(file);

      clearInterval(uploadInterval);
      setProgress(100);
      setLastIngestResult(result);

      // Animate through processing steps quickly
      for (let i = 1; i < processingSteps.length; i++) {
        setCurrentStep(i);
        await new Promise(r => setTimeout(r, 300));
      }

      setUploadState("done");
      await refresh();

      setTimeout(() => {
        setActiveProject(result.extraction_id);
        navigate("/dashboard");
      }, 1200);
    } catch (err) {
      clearInterval(uploadInterval);
      setUploadState("error");
      setUploadError(err.message || "Ingest failed");
    }
  }, [navigate, refresh, setActiveProject, setLastIngestResult]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleIngest(file);
  }, [handleIngest]);

  const handleFileInput = useCallback((e) => {
    const file = e.target.files?.[0];
    if (file) handleIngest(file);
  }, [handleIngest]);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  // Compute stats from real data
  const totalProjects = projects.length;
  const totalEntities = stats?.neo4j_nodes ?? 0;
  const totalRelationships = stats?.neo4j_relationships ?? 0;
  const totalVectors = stats?.faiss_vectors ?? 0;

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-background">
      {/* Top bar */}
      <header className="flex items-center justify-between border-b border-border px-6 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
            <Shield className="h-5 w-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-wider text-foreground">FORENSIQ</h1>
            <p className="text-[10px] font-mono tracking-widest text-muted-foreground">COMMAND CENTER</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button onClick={toggleTheme} className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground">
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          <div className="flex items-center gap-3 rounded-lg border border-border bg-card px-3 py-1.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary/15 text-[10px] font-bold text-primary">
              {user?.avatar}
            </div>
            <div>
              <p className="text-xs font-semibold text-foreground">{user?.name}</p>
              <p className="text-[10px] text-muted-foreground">{user?.role}</p>
            </div>
          </div>
          <button onClick={handleLogout} className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive">
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-y-auto scrollbar-thin p-6">
        <div className="mx-auto max-w-6xl space-y-6">
          {/* Welcome */}
          <div>
            <h2 className="text-xl font-bold text-foreground">Welcome, {user?.name?.split(" ").pop()}</h2>
            <p className="text-sm text-muted-foreground">{user?.department} • {new Date().toLocaleDateString("en-IN", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}</p>
          </div>

          {/* Stats row - REAL data from backend */}
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: "Devices Ingested", value: totalProjects, icon: FolderOpen, color: "text-primary" },
              { label: "Neo4j Entities", value: totalEntities, icon: Users, color: "text-success" },
              { label: "Relationships", value: totalRelationships, icon: Database, color: "text-accent" },
              { label: "FAISS Vectors", value: totalVectors, icon: Cpu, color: "text-chart-5" },
            ].map((stat, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="rounded-xl border border-border bg-card p-4"
              >
                <div className="flex items-center justify-between">
                  <p className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">{stat.label}</p>
                  <stat.icon className={`h-4 w-4 ${stat.color}`} />
                </div>
                <p className="mt-2 text-2xl font-bold text-foreground">{caseLoading ? "…" : stat.value}</p>
              </motion.div>
            ))}
          </div>

          <div className="grid grid-cols-3 gap-6">
            {/* Upload section */}
            <div className="col-span-1">
              <h3 className="mb-3 text-xs font-mono uppercase tracking-widest text-muted-foreground">New Case — Upload UFDR / CLBE</h3>
              <AnimatePresence mode="wait">
                {uploadState === "idle" ? (
                  <motion.label
                    key="idle"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onDragOver={e => e.preventDefault()}
                    onDrop={handleDrop}
                    className="group flex cursor-pointer flex-col items-center gap-3 rounded-xl border-2 border-dashed border-border bg-card p-8 transition-all hover:border-primary/50 hover:bg-primary/5"
                  >
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted group-hover:bg-primary/10 transition-colors">
                      <Upload className="h-6 w-6 text-muted-foreground group-hover:text-primary transition-colors" />
                    </div>
                    <div className="text-center">
                      <p className="text-sm font-semibold text-foreground">
                        Drop file or <span className="text-primary underline underline-offset-2">browse</span>
                      </p>
                      <p className="mt-1 text-[10px] text-muted-foreground">.ufdr, .clbe, .zip — Processed by ForensIQ backend</p>
                    </div>
                    <input type="file" className="hidden" onChange={handleFileInput} accept=".ufdr,.ufd,.clbe,.zip,.tar,.gz" />
                  </motion.label>
                ) : (
                  <motion.div
                    key="progress"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="rounded-xl border border-border bg-card p-5"
                  >
                    <div className="mb-3 flex items-center gap-2">
                      <FileText className="h-4 w-4 text-primary" />
                      <span className="text-xs font-semibold text-foreground truncate">{fileName}</span>
                      {uploadState === "done" && <CheckCircle className="ml-auto h-4 w-4 text-success" />}
                    </div>

                    {uploadState === "uploading" && (
                      <div>
                        <div className="mb-1 flex justify-between">
                          <span className="text-[10px] font-mono text-muted-foreground">Uploading…</span>
                          <span className="text-[10px] font-mono text-primary">{Math.round(progress)}%</span>
                        </div>
                        <div className="h-1 w-full overflow-hidden rounded-full bg-muted">
                          <motion.div className="h-full rounded-full bg-primary" animate={{ width: `${progress}%` }} />
                        </div>
                      </div>
                    )}

                    {(uploadState === "processing" || uploadState === "done") && (
                      <div className="space-y-1.5">
                        {processingSteps.map((step, i) => {
                          const isDone = i < currentStep;
                          const isCurrent = i === currentStep && uploadState === "processing";
                          return (
                            <div key={i} className="flex items-center gap-2">
                              {isDone ? <CheckCircle className="h-3 w-3 text-success flex-shrink-0" /> : isCurrent ? <Loader2 className="h-3 w-3 animate-spin text-primary flex-shrink-0" /> : <div className="h-3 w-3 rounded-full border border-border flex-shrink-0" />}
                              <span className={`text-[10px] font-mono ${isDone ? "text-muted-foreground" : isCurrent ? "text-foreground" : "text-muted-foreground/40"}`}>{step}</span>
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {uploadState === "done" && (
                      <p className="mt-3 text-center text-xs font-semibold text-success">Entering case dashboard…</p>
                    )}

                    {uploadState === "error" && (
                      <div className="mt-3 space-y-2">
                        <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2">
                          <AlertCircle className="h-3.5 w-3.5 flex-shrink-0 text-destructive mt-0.5" />
                          <p className="text-xs text-destructive">{uploadError}</p>
                        </div>
                        <button
                          onClick={() => { setUploadState("idle"); setUploadError(""); }}
                          className="w-full rounded-lg border border-border bg-secondary py-1.5 text-xs font-semibold text-foreground hover:bg-secondary/80 transition-colors"
                        >
                          Try Again
                        </button>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Device / Project list — REAL from backend */}
            <div className="col-span-2">
              <h3 className="mb-3 text-xs font-mono uppercase tracking-widest text-muted-foreground">
                Ingested Devices {projects.length > 0 && `(${projects.length})`}
              </h3>

              {caseLoading ? (
                <div className="flex items-center gap-2 p-8 justify-center text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-xs">Loading projects…</span>
                </div>
              ) : projects.length === 0 ? (
                <div className="rounded-xl border border-dashed border-border bg-card p-8 text-center">
                  <FolderOpen className="mx-auto h-8 w-8 text-muted-foreground/30 mb-2" />
                  <p className="text-sm text-muted-foreground">No devices ingested yet</p>
                  <p className="text-[10px] text-muted-foreground/60 mt-1">Upload a .clbe or .ufdr file to get started</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {projects.map((project, i) => (
                    <motion.div
                      key={project.project_id}
                      initial={{ opacity: 0, x: 10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      onClick={() => {
                        setActiveProject(project.project_id);
                        navigate("/dashboard");
                      }}
                      className="group cursor-pointer rounded-xl border border-border bg-card p-4 transition-all hover:border-primary/40 hover:shadow-md"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-mono font-bold text-primary">{project.project_id.slice(0, 8)}…</span>
                            <span className="rounded-md bg-success/15 text-success px-1.5 py-0.5 text-[9px] font-bold">Ingested</span>
                          </div>
                          <p className="mt-1 text-sm font-semibold text-foreground group-hover:text-primary transition-colors">{project.name}</p>
                          <p className="mt-0.5 text-[11px] text-muted-foreground leading-relaxed">
                            Extraction: {project.extraction_id.slice(0, 12)}… • {project.page_count} pages parsed
                          </p>
                        </div>
                      </div>
                      <div className="mt-2 flex items-center gap-4 text-[10px] font-mono text-muted-foreground">
                        <span>{project.node_count} entities</span>
                        <span>{project.page_count} pages</span>
                        {project.created_at && (
                          <span className="ml-auto">{new Date(project.created_at).toLocaleDateString("en-IN")}</span>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
