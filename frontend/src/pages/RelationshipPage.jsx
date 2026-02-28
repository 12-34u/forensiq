import { useState, useEffect, useMemo, useCallback } from "react";
import { motion } from "framer-motion";
import { ZoomIn, ZoomOut, Eye, Users, Loader2, RefreshCw, Search } from "lucide-react";
import { graphFull, graphProject, graphSearch, listProjects } from "@/lib/api";
import { useCase } from "@/contexts/CaseContext";

// Color nodes by their Neo4j label
const labelStyles = {
  Person:       { bg: "fill-destructive/20", border: "stroke-destructive",  text: "text-destructive" },
  PhoneNumber:  { bg: "fill-accent/20",      border: "stroke-accent",       text: "text-accent" },
  EmailAddress: { bg: "fill-chart-5/20",      border: "stroke-chart-5",      text: "text-chart-5" },
  Device:       { bg: "fill-primary/20",      border: "stroke-primary",      text: "text-primary" },
  App:          { bg: "fill-success/20",      border: "stroke-success",      text: "text-success" },
  Account:      { bg: "fill-chart-5/20",      border: "stroke-chart-5",      text: "text-chart-5" },
  Location:     { bg: "fill-accent/20",       border: "stroke-accent",       text: "text-accent" },
  Organization: { bg: "fill-primary/20",      border: "stroke-primary",      text: "text-primary" },
  URL:          { bg: "fill-muted",           border: "stroke-muted-foreground", text: "text-muted-foreground" },
  Page:         { bg: "fill-muted",           border: "stroke-muted-foreground", text: "text-muted-foreground" },
  Project:      { bg: "fill-primary/30",      border: "stroke-primary",      text: "text-primary" },
  File:         { bg: "fill-accent/20",       border: "stroke-accent",       text: "text-accent" },
};

const defaultStyle = { bg: "fill-muted", border: "stroke-muted-foreground", text: "text-muted-foreground" };

const relColors = {
  MESSAGED:   "stroke-accent",
  CALLED:     "stroke-destructive",
  HAS_PHONE:  "stroke-primary",
  HAS_EMAIL:  "stroke-chart-5",
  OWNS:       "stroke-success",
  USES_APP:   "stroke-success",
  PART_OF:    "stroke-primary/50",
  LOCATED_AT: "stroke-accent",
  KNOWS:      "stroke-muted-foreground",
};

/** Simple force-directed layout — runs synchronously for up to ~500 nodes */
function computeLayout(nodes, edges, width = 800, height = 500) {
  if (nodes.length === 0) return [];

  // Initialize positions in a circle
  const cx = width / 2, cy = height / 2;
  const radius = Math.min(width, height) * 0.38;
  const positions = nodes.map((n, i) => ({
    id: n.id,
    x: cx + radius * Math.cos((2 * Math.PI * i) / nodes.length),
    y: cy + radius * Math.sin((2 * Math.PI * i) / nodes.length),
    vx: 0, vy: 0,
  }));
  const posMap = Object.fromEntries(positions.map(p => [p.id, p]));

  // Build adjacency lookup
  const edgeList = edges
    .filter(e => posMap[e.source] && posMap[e.target])
    .map(e => ({ s: posMap[e.source], t: posMap[e.target] }));

  // Run ~80 iterations of simple force simulation
  const iterations = 80;
  const repulsion = 5000;
  const attraction = 0.005;
  const damping = 0.85;

  for (let iter = 0; iter < iterations; iter++) {
    // Repulsion between all pairs (Barnes-Hut would be better for large graphs)
    for (let i = 0; i < positions.length; i++) {
      for (let j = i + 1; j < positions.length; j++) {
        const a = positions[i], b = positions[j];
        let dx = a.x - b.x, dy = a.y - b.y;
        let dist = Math.sqrt(dx * dx + dy * dy) || 1;
        let force = repulsion / (dist * dist);
        let fx = (dx / dist) * force, fy = (dy / dist) * force;
        a.vx += fx; a.vy += fy;
        b.vx -= fx; b.vy -= fy;
      }
    }
    // Attraction along edges
    for (const { s, t } of edgeList) {
      let dx = t.x - s.x, dy = t.y - s.y;
      let dist = Math.sqrt(dx * dx + dy * dy) || 1;
      let force = attraction * dist;
      let fx = (dx / dist) * force, fy = (dy / dist) * force;
      s.vx += fx; s.vy += fy;
      t.vx -= fx; t.vy -= fy;
    }
    // Center gravity
    for (const p of positions) {
      p.vx += (cx - p.x) * 0.001;
      p.vy += (cy - p.y) * 0.001;
    }
    // Apply velocities
    for (const p of positions) {
      p.x += p.vx; p.y += p.vy;
      p.vx *= damping; p.vy *= damping;
      // Clamp to bounds
      p.x = Math.max(40, Math.min(width - 40, p.x));
      p.y = Math.max(40, Math.min(height - 40, p.y));
    }
  }
  return positions;
}

export default function RelationshipPage() {
  const [selectedNode, setSelectedNode] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [activeSearch, setActiveSearch] = useState(""); // tracks last executed search
  const [projectFilter, setProjectFilter] = useState("_init_"); // sentinel – will be set from activeProject
  const [projects, setProjects] = useState([]);
  const { activeProject } = useCase();

  // Fetch projects for filter dropdown
  useEffect(() => {
    listProjects().then(setProjects).catch(() => {});
  }, []);

  // Auto-select project filter from activeProject context (only on initial load)
  useEffect(() => {
    if (projectFilter === "_init_") {
      setProjectFilter(activeProject || "all");
    }
  }, [activeProject, projectFilter]);

  // Fetch graph data (project-filtered view)
  const fetchGraph = useCallback(async () => {
    if (projectFilter === "_init_") return; // wait for project filter to initialise
    setLoading(true);
    setError("");
    setActiveSearch(""); // clear search mode
    try {
      let data;
      const pid = projectFilter !== "all" ? projectFilter : null;
      if (pid) {
        try {
          data = await graphProject(pid);
        } catch (err) {
          // If project has no graph data (404), show empty instead of falling back to all
          if (err.message?.includes("404") || err.message?.includes("not found")) {
            setGraphData({ nodes: [], edges: [], node_count: 0, edge_count: 0 });
            return;
          }
          throw err;
        }
      } else {
        data = await graphFull({ limit: 500 });
      }
      setGraphData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [projectFilter]);

  useEffect(() => { fetchGraph(); }, [fetchGraph]);

  // Search by entity name
  const handleSearch = async () => {
    const term = searchTerm.trim();
    if (!term) {
      // Empty search — go back to project view
      setActiveSearch("");
      fetchGraph();
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await graphSearch(term);
      setGraphData(data);
      setActiveSearch(term);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Refresh — re-runs search if in search mode, otherwise project fetch
  const handleRefresh = async () => {
    if (activeSearch) {
      setLoading(true);
      setError("");
      try {
        const data = await graphSearch(activeSearch);
        setGraphData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    } else {
      fetchGraph();
    }
  };

  // Compute layout
  const layout = useMemo(
    () => computeLayout(graphData.nodes || [], graphData.edges || []),
    [graphData]
  );
  const posMap = useMemo(
    () => Object.fromEntries(layout.map(p => [p.id, p])),
    [layout]
  );

  // Get display name from node properties
  const getNodeName = (node) => {
    const p = node.properties || {};
    return p.name || p.number || p.address || p.app_name || p.url || p.page_id?.slice(0, 8) || node.label;
  };

  const selectedEntity = graphData.nodes.find(n => n.id === selectedNode);
  const connectedEdges = graphData.edges.filter(e => e.source === selectedNode || e.target === selectedNode);

  // Unique labels for legend
  const uniqueLabels = [...new Set(graphData.nodes.map(n => n.label))];

  return (
    <div className="flex h-full">
      {/* Graph Area */}
      <div className="flex-1 flex flex-col">
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <div>
            <h2 className="text-lg font-bold text-foreground">Dynamic Relationship & Entity Map</h2>
            <p className="text-xs text-muted-foreground">
              {graphData.node_count ?? graphData.nodes.length} entities — {graphData.edge_count ?? graphData.edges.length} connections
              {loading && " (loading…)"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {/* Project filter */}
            <select
              value={projectFilter}
              onChange={e => setProjectFilter(e.target.value)}
              className="rounded-md border border-border bg-card px-2 py-1.5 text-[10px] font-mono text-foreground"
            >
              <option value="all">All Projects</option>
              {projects.map(p => (
                <option key={p.project_id} value={p.project_id}>{p.name}</option>
              ))}
            </select>
            {/* Search */}
            <div className="flex items-center gap-1">
              <input
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleSearch()}
                placeholder="Search entity…"
                className="w-32 rounded-md border border-border bg-card px-2 py-1.5 text-[10px] text-foreground placeholder:text-muted-foreground"
              />
              <button onClick={handleSearch} className="rounded-md bg-secondary p-2 text-secondary-foreground hover:bg-secondary/80">
                <Search className="h-3.5 w-3.5" />
              </button>
            </div>
            <button onClick={handleRefresh} className="rounded-md bg-secondary p-2 text-secondary-foreground hover:bg-secondary/80">
              <RefreshCw className="h-4 w-4" />
            </button>
            <button onClick={() => setZoom(z => Math.max(0.3, z - 0.1))} className="rounded-md bg-secondary p-2 text-secondary-foreground hover:bg-secondary/80">
              <ZoomOut className="h-4 w-4" />
            </button>
            <span className="text-xs font-mono text-muted-foreground">{Math.round(zoom * 100)}%</span>
            <button onClick={() => setZoom(z => Math.min(2.0, z + 0.1))} className="rounded-md bg-secondary p-2 text-secondary-foreground hover:bg-secondary/80">
              <ZoomIn className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 border-b border-border px-6 py-2 flex-wrap">
          {uniqueLabels.map(label => {
            const styles = labelStyles[label] || defaultStyle;
            return (
              <div key={label} className="flex items-center gap-1.5">
                <div className={`h-3 w-3 rounded-full border-2 ${styles.border.replace("stroke-", "border-")} ${styles.bg.replace("fill-", "bg-")}`} />
                <span className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">{label}</span>
              </div>
            );
          })}
        </div>

        {/* SVG Graph */}
        <div className="flex-1 relative overflow-hidden bg-background">
          {loading ? (
            <div className="flex h-full items-center justify-center gap-2 text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className="text-sm">Loading graph…</span>
            </div>
          ) : error ? (
            <div className="flex h-full items-center justify-center text-sm text-destructive">{error}</div>
          ) : graphData.nodes.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-muted-foreground">
              <Users className="h-10 w-10 mb-3 opacity-30" />
              <p className="text-sm">No graph data available</p>
              <p className="text-[10px] mt-1">Ingest a .clbe file first, then come back</p>
            </div>
          ) : (
            <svg
              width="100%"
              height="100%"
              viewBox="0 0 800 500"
              className="absolute inset-0"
              style={{ transform: `scale(${zoom})`, transformOrigin: "center" }}
            >
              {/* Edges */}
              {graphData.edges.map((edge, i) => {
                const src = posMap[edge.source];
                const tgt = posMap[edge.target];
                if (!src || !tgt) return null;
                const isHighlighted = selectedNode === edge.source || selectedNode === edge.target;
                return (
                  <g key={i}>
                    <line
                      x1={src.x} y1={src.y}
                      x2={tgt.x} y2={tgt.y}
                      className={relColors[edge.type] || "stroke-muted-foreground"}
                      strokeWidth={isHighlighted ? 2.5 : 1}
                      strokeOpacity={selectedNode ? (isHighlighted ? 0.8 : 0.1) : 0.35}
                    />
                    {isHighlighted && (
                      <text
                        x={(src.x + tgt.x) / 2}
                        y={(src.y + tgt.y) / 2 - 6}
                        textAnchor="middle"
                        className="fill-muted-foreground text-[8px] font-mono"
                      >
                        {edge.type}
                      </text>
                    )}
                  </g>
                );
              })}

              {/* Nodes */}
              {graphData.nodes.map(node => {
                const pos = posMap[node.id];
                if (!pos) return null;
                const styles = labelStyles[node.label] || defaultStyle;
                const isSelected = selectedNode === node.id;
                const isConnected = connectedEdges.some(e => e.source === node.id || e.target === node.id);
                const dimmed = selectedNode && !isSelected && !isConnected;
                const displayName = getNodeName(node);

                return (
                  <g
                    key={node.id}
                    className="cursor-pointer"
                    onClick={() => setSelectedNode(isSelected ? null : node.id)}
                    opacity={dimmed ? 0.15 : 1}
                  >
                    <circle
                      cx={pos.x} cy={pos.y}
                      r={isSelected ? 24 : 18}
                      className={`${styles.bg} ${styles.border}`}
                      strokeWidth={isSelected ? 3 : 2}
                      style={isSelected ? { filter: "drop-shadow(0 0 8px currentColor)" } : undefined}
                    />
                    <text
                      x={pos.x} y={pos.y + 30}
                      textAnchor="middle"
                      className={`${styles.text} text-[8px] font-semibold`}
                    >
                      {displayName.length > 14 ? displayName.slice(0, 14) + "…" : displayName}
                    </text>
                    <text
                      x={pos.x} y={pos.y + 4}
                      textAnchor="middle"
                      className="fill-foreground text-[9px] font-bold font-mono"
                    >
                      {node.label.slice(0, 3).toUpperCase()}
                    </text>
                  </g>
                );
              })}
            </svg>
          )}
        </div>
      </div>

      {/* Detail Panel */}
      <div className="w-72 border-l border-border bg-card overflow-y-auto scrollbar-thin">
        {selectedEntity ? (
          <motion.div
            key={selectedEntity.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="p-5"
          >
            <div className="flex items-center gap-2 mb-4">
              <Eye className="h-4 w-4 text-primary" />
              <h3 className="text-sm font-bold text-foreground">Entity Profile</h3>
            </div>
            <div className="space-y-3">
              <div>
                <p className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">Name / ID</p>
                <p className="text-sm font-semibold text-foreground">{getNodeName(selectedEntity)}</p>
              </div>
              <div>
                <p className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">Label</p>
                <span className={`inline-block rounded px-2 py-0.5 text-[10px] font-semibold uppercase ${(labelStyles[selectedEntity.label] || defaultStyle).text} bg-secondary`}>
                  {selectedEntity.label}
                </span>
              </div>

              {/* All properties */}
              {Object.entries(selectedEntity.properties || {}).map(([key, val]) => (
                <div key={key}>
                  <p className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">{key.replace(/_/g, " ")}</p>
                  <p className="text-xs font-mono text-foreground break-all">{String(val)}</p>
                </div>
              ))}

              <div className="pt-3 border-t border-border">
                <p className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground mb-2">Connections ({connectedEdges.length})</p>
                <div className="space-y-1.5">
                  {connectedEdges.map((edge, i) => {
                    const otherNodeId = edge.source === selectedNode ? edge.target : edge.source;
                    const other = graphData.nodes.find(n => n.id === otherNodeId);
                    return (
                      <div key={i} className="flex items-center justify-between rounded-md bg-muted px-2.5 py-1.5">
                        <span className="text-xs text-foreground">{other ? getNodeName(other) : "?"}</span>
                        <span className="text-[10px] font-mono text-muted-foreground">{edge.type}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </motion.div>
        ) : (
          <div className="flex h-full flex-col items-center justify-center p-5 text-center">
            <Users className="h-10 w-10 text-muted-foreground/30 mb-3" />
            <p className="text-sm text-muted-foreground">Click a node to inspect</p>
            <p className="text-[10px] text-muted-foreground/60 mt-1">Entity details and connections will appear here</p>
          </div>
        )}
      </div>
    </div>
  );
}
