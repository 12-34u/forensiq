import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ShieldAlert, Search, Eye, ChevronDown, Loader2, RefreshCw,
  AlertTriangle, FileWarning, EyeOff, Fingerprint, DollarSign, PenTool,
  Filter
} from "lucide-react";
import { getRiskIntel, listProjects } from "@/lib/api";
import { useCase } from "@/contexts/CaseContext";

const categoryConfig = {
  counter_intel:        { icon: <EyeOff className="h-4 w-4" />,        color: "text-destructive",        bg: "bg-destructive/10", label: "Counter-Intel" },
  evidence_fabrication: { icon: <PenTool className="h-4 w-4" />,       color: "text-accent",             bg: "bg-accent/10",      label: "Evidence Fabrication" },
  anti_forensic:        { icon: <Fingerprint className="h-4 w-4" />,   color: "text-chart-5",            bg: "bg-chart-5/10",     label: "Anti-Forensic" },
  obfuscation:          { icon: <EyeOff className="h-4 w-4" />,        color: "text-primary",            bg: "bg-primary/10",     label: "Obfuscation" },
  financial_fraud:      { icon: <DollarSign className="h-4 w-4" />,    color: "text-accent",             bg: "bg-accent/10",      label: "Financial Fraud" },
  evidence_tampering:   { icon: <FileWarning className="h-4 w-4" />,   color: "text-destructive",        bg: "bg-destructive/10", label: "Evidence Tampering" },
};

const severityStyles = {
  critical: "border-destructive/40 bg-destructive/5",
  high:     "border-accent/40 bg-accent/5",
  medium:   "border-primary/40 bg-primary/5",
  low:      "border-border bg-muted/50",
};

const severityBadge = {
  critical: "bg-destructive text-destructive-foreground",
  high:     "bg-accent text-accent-foreground",
  medium:   "bg-primary text-primary-foreground",
  low:      "bg-muted text-muted-foreground",
};

const overallRiskColor = {
  CRITICAL: "text-destructive",
  HIGH:     "text-accent",
  MEDIUM:   "text-primary",
  LOW:      "text-muted-foreground",
  UNKNOWN:  "text-muted-foreground",
};

export default function RiskIntelPage() {
  const [filterCategory, setFilterCategory] = useState("all");
  const [filterSeverity, setFilterSeverity] = useState("all");
  const [expandedHit, setExpandedHit] = useState(null);
  const [riskData, setRiskData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState("");
  const { activeProject } = useCase();

  // Fetch projects
  useEffect(() => {
    listProjects().then(p => {
      setProjects(p);
      if (activeProject) {
        setSelectedProject(activeProject);
      } else if (p.length > 0) {
        setSelectedProject(p[0].project_id);
      }
    }).catch(() => {});
  }, [activeProject]);

  // Fetch risk intel when project changes
  useEffect(() => {
    if (!selectedProject) return;
    setLoading(true);
    setError("");
    setRiskData(null);
    getRiskIntel(selectedProject)
      .then(setRiskData)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [selectedProject]);

  const handleRefresh = () => {
    if (!selectedProject) return;
    setLoading(true);
    setError("");
    getRiskIntel(selectedProject)
      .then(setRiskData)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  };

  // Filtered hits
  const filteredHits = (riskData?.hits || []).filter(h => {
    if (filterCategory !== "all" && h.category !== filterCategory) return false;
    if (filterSeverity !== "all" && h.severity !== filterSeverity) return false;
    return true;
  });

  const summary = riskData?.summary || {};
  const byCat = summary.by_category || {};
  const bySev = summary.by_severity || { critical: 0, high: 0, medium: 0, low: 0 };

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-destructive/10">
            <ShieldAlert className="h-5 w-5 text-destructive" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-foreground">Risk Intelligence</h2>
            <p className="text-xs text-muted-foreground">
              Rule-based detection of misleading, deceptive &amp; anti-forensic indicators
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={selectedProject}
            onChange={e => setSelectedProject(e.target.value)}
            className="rounded-md border border-border bg-card px-2 py-1.5 text-[10px] font-mono text-foreground"
          >
            <option value="">Select project…</option>
            {projects.map(p => (
              <option key={p.project_id} value={p.project_id}>{p.name}</option>
            ))}
          </select>
          <button onClick={handleRefresh} disabled={loading || !selectedProject} className="rounded-md bg-secondary p-2 text-secondary-foreground hover:bg-secondary/80 disabled:opacity-50">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Risk Summary Bar */}
      {riskData && (
        <div className="flex items-center gap-6 border-b border-border px-6 py-3 bg-card/50">
          <div className="flex items-center gap-2">
            <AlertTriangle className={`h-5 w-5 ${overallRiskColor[summary.overall_risk] || "text-muted-foreground"}`} />
            <span className={`text-sm font-bold ${overallRiskColor[summary.overall_risk] || ""}`}>
              {summary.overall_risk || "UNKNOWN"} RISK
            </span>
          </div>
          <div className="flex items-center gap-3 text-[10px] font-mono">
            <span className="text-destructive">{bySev.critical} critical</span>
            <span className="text-accent">{bySev.high} high</span>
            <span className="text-primary">{bySev.medium} medium</span>
            <span className="text-muted-foreground">{bySev.low} low</span>
          </div>
          <div className="ml-auto text-[10px] text-muted-foreground">
            {riskData.total_pages_scanned} pages scanned · {riskData.total_hits} findings
          </div>
        </div>
      )}

      {/* Category chips + filters */}
      {riskData && (
        <div className="flex items-center gap-2 border-b border-border px-6 py-2 flex-wrap">
          <Filter className="h-3.5 w-3.5 text-muted-foreground" />
          <button
            onClick={() => setFilterCategory("all")}
            className={`rounded-full px-2.5 py-1 text-[10px] font-mono transition-colors ${
              filterCategory === "all" ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
            }`}
          >
            All ({riskData.total_hits})
          </button>
          {Object.entries(byCat).map(([cat, count]) => {
            const cfg = categoryConfig[cat] || { label: cat, color: "text-muted-foreground", bg: "bg-muted" };
            return (
              <button
                key={cat}
                onClick={() => setFilterCategory(filterCategory === cat ? "all" : cat)}
                className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-mono transition-colors ${
                  filterCategory === cat ? `${cfg.bg} ${cfg.color} ring-1 ring-current` : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                }`}
              >
                {cfg.icon}
                {cfg.label} ({count})
              </button>
            );
          })}
          <div className="ml-auto">
            <select
              value={filterSeverity}
              onChange={e => setFilterSeverity(e.target.value)}
              className="rounded-md border border-border bg-card px-2 py-1 text-[10px] font-mono text-foreground"
            >
              <option value="all">All severities</option>
              <option value="critical">Critical only</option>
              <option value="high">High+</option>
              <option value="medium">Medium+</option>
            </select>
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-6 py-4">
        {loading ? (
          <div className="flex h-64 items-center justify-center gap-2 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-sm">Scanning pages for risk indicators…</span>
          </div>
        ) : error ? (
          <div className="flex h-64 items-center justify-center text-sm text-destructive">{error}</div>
        ) : !riskData ? (
          <div className="flex h-64 flex-col items-center justify-center text-muted-foreground">
            <ShieldAlert className="h-10 w-10 mb-3 opacity-30" />
            <p className="text-sm">Select a project to scan for risk indicators</p>
          </div>
        ) : filteredHits.length === 0 ? (
          <div className="flex h-64 flex-col items-center justify-center text-muted-foreground">
            <ShieldAlert className="h-10 w-10 mb-3 opacity-30" />
            <p className="text-sm">No risk indicators found matching current filters</p>
          </div>
        ) : (
          <AnimatePresence mode="popLayout">
            <div className="space-y-3">
              {filteredHits.map((hit, i) => {
                const cfg = categoryConfig[hit.category] || { icon: <AlertTriangle className="h-4 w-4" />, color: "text-muted-foreground", bg: "bg-muted", label: hit.category };
                const isExpanded = expandedHit === i;

                return (
                  <motion.div
                    key={`${hit.rule_id}-${hit.page_id}`}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ delay: i * 0.03 }}
                    className={`rounded-lg border p-4 transition-all cursor-pointer ${severityStyles[hit.severity]} ${isExpanded ? "ring-1 ring-current" : ""}`}
                    onClick={() => setExpandedHit(isExpanded ? null : i)}
                  >
                    {/* Header row */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3 flex-1">
                        <div className={`mt-0.5 ${cfg.color}`}>{cfg.icon}</div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="text-sm font-semibold text-foreground">{hit.title}</h3>
                            <span className={`rounded-full px-2 py-0.5 text-[9px] font-bold uppercase ${severityBadge[hit.severity]}`}>
                              {hit.severity}
                            </span>
                            <span className={`rounded-full px-2 py-0.5 text-[9px] font-mono ${cfg.bg} ${cfg.color}`}>
                              {cfg.label}
                            </span>
                          </div>
                          <p className="mt-1 text-xs text-muted-foreground">{hit.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono text-muted-foreground">
                          {Math.round(hit.confidence * 100)}%
                        </span>
                        <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${isExpanded ? "rotate-180" : ""}`} />
                      </div>
                    </div>

                    {/* Evidence excerpt - always visible */}
                    <div className="mt-3 rounded-md bg-background/50 border border-border/50 px-3 py-2">
                      <p className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground mb-1">Evidence Excerpt</p>
                      <p className="text-xs text-foreground font-mono leading-relaxed">"{hit.evidence_excerpt}"</p>
                    </div>

                    {/* Expanded details */}
                    {isExpanded && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mt-3 space-y-2 border-t border-border/50 pt-3"
                      >
                        <div className="grid grid-cols-3 gap-4 text-xs">
                          <div>
                            <p className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">Rule ID</p>
                            <p className="font-mono text-foreground">{hit.rule_id}</p>
                          </div>
                          <div>
                            <p className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">Artifact Type</p>
                            <p className="font-mono text-foreground">{hit.artifact_type}</p>
                          </div>
                          <div>
                            <p className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">Source Device</p>
                            <p className="font-mono text-foreground truncate">{hit.source_device || "—"}</p>
                          </div>
                        </div>
                        <div>
                          <p className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">Page ID</p>
                          <p className="text-xs font-mono text-foreground">{hit.page_id}</p>
                        </div>
                      </motion.div>
                    )}
                  </motion.div>
                );
              })}
            </div>
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
