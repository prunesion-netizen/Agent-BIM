import { useState, useEffect, useCallback } from "react";
import StatusBadge from "./StatusBadge";

/* ── Types ── */

interface LatestVerificationInfo {
  summary_status: string | null;
  fail_count: number | null;
  warning_count: number | null;
  created_at: string;
}

interface ProjectOverviewItem {
  id: number;
  name: string;
  code: string;
  client_name: string | null;
  project_type: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  has_context: boolean;
  has_bep: boolean;
  bep_version: string | null;
  verification_count: number;
  latest_verification: LatestVerificationInfo | null;
}

type TargetTab = "bep" | "chat" | "verifier";

interface Props {
  onSelectProject: (projectId: number, tab: TargetTab) => void;
}

/* ── Helpers ── */

const PROJECT_TYPE_LABELS: Record<string, string> = {
  residential: "Rezidențial",
  commercial: "Comercial",
  industrial: "Industrial",
  infrastructure: "Infrastructură",
  renovation: "Renovare",
  mixed_use: "Mixt",
};

function formatDate(iso: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("ro-RO", { day: "2-digit", month: "short", year: "numeric" });
}

function getVerifBadgeClass(status: string | null): string {
  if (status === "pass") return "dashboard-verif-pass";
  if (status === "warning") return "dashboard-verif-warning";
  if (status === "fail") return "dashboard-verif-fail";
  return "dashboard-verif-none";
}

function getVerifLabel(status: string | null): string {
  if (status === "pass") return "OK";
  if (status === "warning") return "Atenție";
  if (status === "fail") return "Eșuat";
  return "—";
}

/* ── Component ── */

export default function Dashboard({ onSelectProject }: Props) {
  const [items, setItems] = useState<ProjectOverviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [filterType, setFilterType] = useState<string>("all");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/projects-overview");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: ProjectOverviewItem[] = await res.json();
      setItems(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Eroare la încărcare");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Client-side filtering
  const filtered = items.filter((p) => {
    const q = search.toLowerCase();
    const matchSearch =
      !q ||
      p.name.toLowerCase().includes(q) ||
      p.code.toLowerCase().includes(q) ||
      (p.client_name ?? "").toLowerCase().includes(q);
    const matchStatus = filterStatus === "all" || p.status === filterStatus;
    const matchType = filterType === "all" || p.project_type === filterType;
    return matchSearch && matchStatus && matchType;
  });

  // Summary stats
  const total = items.length;
  const withBep = items.filter((p) => p.has_bep).length;
  const verifiedOk = items.filter(
    (p) => p.latest_verification?.summary_status === "pass"
  ).length;
  const withIssues = items.filter((p) => {
    const v = p.latest_verification;
    return v && (v.summary_status === "fail" || v.summary_status === "warning");
  }).length;

  // Unique project types for filter dropdown
  const projectTypes = Array.from(
    new Set(items.map((p) => p.project_type).filter(Boolean) as string[])
  );

  return (
    <div className="demo-container">
      <header className="demo-header">
        <div className="demo-brand">
          <div className="demo-logo">▦</div>
          <div>
            <h1>Dashboard Proiecte BIM</h1>
            <p className="demo-subtitle">
              Vedere de ansamblu a tuturor proiectelor
            </p>
          </div>
        </div>
      </header>

      {/* Summary cards */}
      <div className="dashboard-summary-row">
        <div className="dashboard-stat-card">
          <div className="dashboard-stat-value">{total}</div>
          <div className="dashboard-stat-label">Total Proiecte</div>
        </div>
        <div className="dashboard-stat-card">
          <div className="dashboard-stat-value">{withBep}</div>
          <div className="dashboard-stat-label">Cu BEP Generat</div>
        </div>
        <div className="dashboard-stat-card">
          <div className="dashboard-stat-value dashboard-stat-ok">{verifiedOk}</div>
          <div className="dashboard-stat-label">Verificate OK</div>
        </div>
        <div className="dashboard-stat-card">
          <div className="dashboard-stat-value dashboard-stat-warn">{withIssues}</div>
          <div className="dashboard-stat-label">Cu Probleme</div>
        </div>
      </div>

      {/* Filters */}
      <div className="dashboard-filters">
        <input
          className="dashboard-search"
          type="text"
          placeholder="Caută după nume, cod sau client..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="dashboard-filter-select"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
        >
          <option value="all">Toate statusurile</option>
          <option value="new">Nou</option>
          <option value="context_defined">Context definit</option>
          <option value="bep_generated">BEP generat</option>
          <option value="bep_verified_partial">Verificat parțial</option>
          <option value="bep_verified_ok">Verificat OK</option>
        </select>
        <select
          className="dashboard-filter-select"
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
        >
          <option value="all">Toate tipurile</option>
          {projectTypes.map((t) => (
            <option key={t} value={t}>
              {PROJECT_TYPE_LABELS[t] ?? t}
            </option>
          ))}
        </select>
        <button className="btn-outline btn-sm" onClick={loadData} disabled={loading}>
          ↻ Reîncarcă
        </button>
      </div>

      {/* Error / Loading */}
      {error && <p style={{ color: "var(--red-500)", marginTop: 12 }}>{error}</p>}

      {loading ? (
        <p style={{ textAlign: "center", marginTop: 32, color: "var(--gray-500)" }}>
          Se încarcă proiectele...
        </p>
      ) : filtered.length === 0 ? (
        <p style={{ textAlign: "center", marginTop: 32, color: "var(--gray-500)" }}>
          {items.length === 0
            ? "Nu există proiecte. Creează primul proiect din tab-ul Fișa BEP."
            : "Niciun proiect nu corespunde filtrelor."}
        </p>
      ) : (
        <div className="dashboard-table-wrap">
          <table className="dashboard-table">
            <thead>
              <tr>
                <th>Proiect</th>
                <th>Client</th>
                <th>Tip</th>
                <th>Status</th>
                <th>BEP</th>
                <th>Verificare</th>
                <th>Ultima actualizare</th>
                <th>Acțiuni</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <tr key={p.id}>
                  <td>
                    <div className="dashboard-project-cell">
                      <span className="dashboard-project-name">{p.name}</span>
                      <span className="dashboard-project-code">{p.code}</span>
                    </div>
                  </td>
                  <td>{p.client_name ?? "—"}</td>
                  <td>{p.project_type ? (PROJECT_TYPE_LABELS[p.project_type] ?? p.project_type) : "—"}</td>
                  <td>
                    <StatusBadge status={p.status} />
                  </td>
                  <td>
                    <span className={p.has_bep ? "dashboard-bep-yes" : "dashboard-bep-no"}>
                      {p.has_bep ? "Da" : "Nu"}
                    </span>
                    {p.bep_version && (
                      <span className="dashboard-bep-version">v{p.bep_version}</span>
                    )}
                  </td>
                  <td>
                    {p.latest_verification ? (
                      <div className="dashboard-verif-cell">
                        <span className={`dashboard-verif-badge ${getVerifBadgeClass(p.latest_verification.summary_status)}`}>
                          {getVerifLabel(p.latest_verification.summary_status)}
                        </span>
                        {(p.latest_verification.fail_count != null ||
                          p.latest_verification.warning_count != null) && (
                          <span className="dashboard-verif-counts">
                            {p.latest_verification.fail_count
                              ? `${p.latest_verification.fail_count}F`
                              : ""}
                            {p.latest_verification.fail_count &&
                            p.latest_verification.warning_count
                              ? " / "
                              : ""}
                            {p.latest_verification.warning_count
                              ? `${p.latest_verification.warning_count}W`
                              : ""}
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="dashboard-verif-none-text">—</span>
                    )}
                  </td>
                  <td>
                    <span className="dashboard-date-cell">
                      {formatDate(p.updated_at)}
                    </span>
                  </td>
                  <td>
                    <div className="dashboard-actions">
                      <button
                        className="btn-primary btn-sm"
                        onClick={() => onSelectProject(p.id, "bep")}
                        title="Deschide Fișa BEP"
                      >
                        Fișa BEP
                      </button>
                      {p.has_bep && (
                        <button
                          className="btn-outline btn-sm"
                          onClick={() => onSelectProject(p.id, "verifier")}
                          title="Verifică BEP"
                        >
                          Verifică
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
