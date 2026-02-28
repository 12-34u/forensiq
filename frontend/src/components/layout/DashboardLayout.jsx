import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { Search, GitBranch, Clock, AlertTriangle, Sun, Moon, Shield, Home, LogOut, ShieldAlert } from "lucide-react";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/contexts/AuthContext";
import { useCase } from "@/contexts/CaseContext";

const navItems = [
  { path: "/dashboard", label: "NLIQ Chat", icon: Search },
  { path: "/dashboard/relationships", label: "Entity Map", icon: GitBranch },
  { path: "/dashboard/riskintel", label: "Risk Intel", icon: ShieldAlert },
  { path: "/dashboard/anomalies", label: "Anomalies", icon: AlertTriangle },
];

export function DashboardLayout({ children }) {
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const { projects, stats, activeProject } = useCase();
  const navigate = useNavigate();
  const location = useLocation();

  // Find active project info
  const currentProject = projects.find(p => p.project_id === activeProject);
  const projectLabel = currentProject?.name || "All Devices";
  const deviceCount = projects.length;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className="flex w-64 flex-col border-r border-border bg-sidebar">
        {/* Logo */}
        <div className="flex items-center gap-3 border-b border-border px-5 py-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
            <Shield className="h-5 w-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-wider text-foreground">FORENSIQ</h1>
            <p className="text-[10px] font-mono tracking-widest text-muted-foreground">UFDR ANALYSIS</p>
          </div>
        </div>

        {/* Case Info — real data */}
        <div className="border-b border-border px-5 py-3">
          <p className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">Active Device</p>
          <p className="mt-1 text-xs font-semibold text-foreground truncate">{projectLabel}</p>
          {stats && (
            <p className="text-[10px] text-muted-foreground">
              {stats.neo4j_nodes ?? 0} entities • {stats.faiss_vectors ?? 0} vectors
            </p>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(item => {
            const isActive = location.pathname === item.path;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${
                  isActive
                    ? "bg-primary/10 text-primary glow-primary"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                }`}
              >
                <item.icon className={`h-4 w-4 ${isActive ? "text-primary" : ""}`} />
                {item.label}
              </NavLink>
            );
          })}
        </nav>

        {/* Bottom */}
        <div className="border-t border-border px-5 py-3 space-y-1">
          <button
            onClick={() => navigate("/home")}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          >
            <Home className="h-4 w-4" />
            Home
          </button>
          <button
            onClick={toggleTheme}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            {theme === "dark" ? "Light Mode" : "Dark Mode"}
          </button>
          <button
            onClick={() => { logout(); navigate("/"); }}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </button>
          <div className="mt-3 flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-success animate-pulse-glow" />
            <span className="text-[10px] font-mono text-muted-foreground">{deviceCount} Device{deviceCount !== 1 ? "s" : ""} Ingested</span>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-hidden">
        {children}
      </main>
    </div>
  );
}
