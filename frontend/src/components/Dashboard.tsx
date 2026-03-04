import { useState, useEffect, useCallback } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import StatusBadge from "./StatusBadge";
import { useAuth } from "../contexts/AuthProvider";

/* ── Types ── */

export type ProjectOverview = {
  id: number;
  name: string;
  code: string;
  client_name?: string | null;
  project_type?: string | null;
  status: string;
  has_bep: boolean;
  bep_version?: string | null;
  last_bep_generated_at?: string | null;
  has_verifications: boolean;
  last_verification_at?: string | null;
  last_verification_status?: "pass" | "partial" | "fail" | null;
  last_verification_fail_count?: number | null;
  last_verification_warning_count?: number | null;
  health_score: number;
  has_ifc: boolean;
  health_alerts: string[];
  // ISO 19650 fields
  has_eir?: boolean;
  tidp_completion?: number;
  has_raci?: boolean;
  has_security_plan?: boolean;
  clash_open_count?: number;
  bep_cde_state?: string | null;
  updated_at: string;
};

type TargetTab = "bep" | "agent" | "chat" | "verifier";

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

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("ro-RO", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function formatBepCell(p: ProjectOverview): string {
  if (!p.has_bep) return "—";
  const ver = p.bep_version ? `v${p.bep_version}` : "BEP";
  const date = formatDate(p.last_bep_generated_at);
  return date !== "—" ? `${ver} – ${date}` : ver;
}

function formatVerifCell(p: ProjectOverview): string {
  if (!p.has_verifications) return "—";
  const status = p.last_verification_status ?? "—";
  const f = p.last_verification_fail_count ?? 0;
  const w = p.last_verification_warning_count ?? 0;
  const counts = f || w ? ` (${f}F/${w}W)` : "";
  const date = formatDate(p.last_verification_at);
  return `${status}${counts} – ${date}`;
}

function getVerifBadgeClass(status: string | null | undefined): string {
  if (status === "pass") return "dashboard-verif-pass";
  if (status === "warning" || status === "partial") return "dashboard-verif-warning";
  if (status === "fail") return "dashboard-verif-fail";
  return "dashboard-verif-none";
}

function getHealthColor(score: number): string {
  if (score >= 80) return "health-green";
  if (score >= 50) return "health-yellow";
  return "health-red";
}

const STATUS_LABELS: Record<string, string> = {
  new: "Nou",
  context_defined: "Context definit",
  bep_generated: "BEP generat",
  bep_verified_partial: "Verificat partial",
  bep_verified_ok: "Verificat OK",
};

const STATUS_COLORS: Record<string, string> = {
  new: "#9ca3af",
  context_defined: "#60a5fa",
  bep_generated: "#f59e0b",
  bep_verified_partial: "#f97316",
  bep_verified_ok: "#16a34a",
};

/* ── Component ── */

export default function Dashboard({ onSelectProject }: Props) {
  const { authFetch } = useAuth();
  const [items, setItems] = useState<ProjectOverview[]>([]);
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
      const res = await authFetch("/api/projects/overview");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: ProjectOverview[] = await res.json();
      setItems(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Eroare la încărcare");
    } finally {
      setLoading(false);
    }
  }, [authFetch]);

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
    (p) => p.last_verification_status === "pass"
  ).length;
  const withIssues = items.filter(
    (p) =>
      p.last_verification_status === "fail" ||
      p.last_verification_status === "partial"
  ).length;
  const avgHealth = total > 0
    ? Math.round(items.reduce((s, p) => s + p.health_score, 0) / total)
    : 0;

  // Unique project types for filter dropdown
  const projectTypes = Array.from(
    new Set(items.map((p) => p.project_type).filter(Boolean) as string[])
  );

  // Status distribution for donut chart
  const statusCounts = items.reduce<Record<string, number>>((acc, p) => {
    acc[p.status] = (acc[p.status] || 0) + 1;
    return acc;
  }, {});

  const statusChartData = Object.entries(statusCounts).map(([status, count]) => ({
    name: STATUS_LABELS[status] || status,
    value: count,
    fill: STATUS_COLORS[status] || "#9ca3af",
  }));

  return (
    <div className="demo-container">
      <header className="demo-header">
        <div className="demo-brand">
          <div className="demo-logo">▦</div>
          <div>
            <h1>Proiecte BIM</h1>
            <p className="demo-subtitle">
              Vedere de ansamblu a tuturor proiectelor
            </p>
          </div>
        </div>
      </header>

      {/* Summary cards */}
      <div className="dashboard-summary-row dashboard-summary-5">
        <div className="dashboard-stat-card">
          <div className="dashboard-stat-value">{total}</div>
          <div className="dashboard-stat-label">Total Proiecte</div>
        </div>
        <div className="dashboard-stat-card">
          <div className="dashboard-stat-value">{withBep}</div>
          <div className="dashboard-stat-label">Cu BEP Generat</div>
        </div>
        <div className="dashboard-stat-card">
          <div className="dashboard-stat-value dashboard-stat-ok">
            {verifiedOk}
          </div>
          <div className="dashboard-stat-label">Verificate OK</div>
        </div>
        <div className="dashboard-stat-card">
          <div className="dashboard-stat-value dashboard-stat-warn">
            {withIssues}
          </div>
          <div className="dashboard-stat-label">Cu Probleme</div>
        </div>
        <div className="dashboard-stat-card">
          <div className={`dashboard-stat-value dashboard-stat-health ${getHealthColor(avgHealth)}`}>
            {avgHealth}%
          </div>
          <div className="dashboard-stat-label">Scor Mediu Sanatate</div>
        </div>
      </div>

      {/* Status distribution chart */}
      {items.length > 0 && (
        <div className="dashboard-charts-row">
          <div className="dashboard-chart-card">
            <h3 className="dashboard-chart-title">Distributie Status Proiecte</h3>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={statusChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={3}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {statusChartData.map((entry, idx) => (
                    <Cell key={idx} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

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
        <button
          className="btn-outline btn-sm"
          onClick={loadData}
          disabled={loading}
        >
          ↻ Reîncarcă
        </button>
      </div>

      {/* Error / Loading */}
      {error && (
        <p style={{ color: "var(--red-500)", marginTop: 12 }}>{error}</p>
      )}

      {loading ? (
        <p
          style={{
            textAlign: "center",
            marginTop: 32,
            color: "var(--gray-500)",
          }}
        >
          Se încarcă proiectele...
        </p>
      ) : filtered.length === 0 ? (
        <p
          style={{
            textAlign: "center",
            marginTop: 32,
            color: "var(--gray-500)",
          }}
        >
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
                <th>Status BIM</th>
                <th>Sanatate</th>
                <th>BEP</th>
                <th>Ultima verificare</th>
                <th>Actiuni</th>
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
                  <td>
                    {p.project_type
                      ? (PROJECT_TYPE_LABELS[p.project_type] ?? p.project_type)
                      : "—"}
                  </td>
                  <td>
                    <StatusBadge status={p.status} />
                  </td>
                  <td>
                    <div className="dashboard-health-cell">
                      <div className="dashboard-health-bar-track">
                        <div
                          className={`dashboard-health-bar-fill ${getHealthColor(p.health_score)}`}
                          style={{ width: `${p.health_score}%` }}
                        />
                      </div>
                      <span className={`dashboard-health-value ${getHealthColor(p.health_score)}`}>
                        {p.health_score}%
                      </span>
                      <div className="dashboard-presence-icons">
                        <span className={p.has_bep ? "presence-ok" : "presence-no"} title="BEP generat">
                          {p.has_bep ? "\u2713" : "\u2717"} BEP
                        </span>
                        <span className={p.has_ifc ? "presence-ok" : "presence-no"} title="Model IFC importat">
                          {p.has_ifc ? "\u2713" : "\u2717"} IFC
                        </span>
                        <span className={p.has_verifications ? "presence-ok" : "presence-no"} title="Verificare BEP efectuata">
                          {p.has_verifications ? "\u2713" : "\u2717"} Verif
                        </span>
                        <span className={p.has_eir ? "presence-ok" : "presence-no"} title="EIR definit">
                          {p.has_eir ? "\u2713" : "\u2717"} EIR
                        </span>
                        <span className={p.has_raci ? "presence-ok" : "presence-no"} title="RACI definit">
                          {p.has_raci ? "\u2713" : "\u2717"} RACI
                        </span>
                      </div>
                    </div>
                  </td>
                  <td>
                    {p.has_bep ? (
                      <span className="dashboard-bep-yes">
                        {formatBepCell(p)}
                      </span>
                    ) : (
                      <span className="dashboard-bep-no">—</span>
                    )}
                  </td>
                  <td>
                    {p.has_verifications ? (
                      <div className="dashboard-verif-cell">
                        <span
                          className={`dashboard-verif-badge ${getVerifBadgeClass(p.last_verification_status)}`}
                        >
                          {formatVerifCell(p)}
                        </span>
                      </div>
                    ) : (
                      <span className="dashboard-verif-none-text">—</span>
                    )}
                  </td>
                  <td>
                    <div className="dashboard-actions">
                      <button
                        className="btn-primary btn-sm"
                        onClick={() => onSelectProject(p.id, "agent")}
                        title="Deschide Agent BIM"
                      >
                        Agent
                      </button>
                      <button
                        className="btn-outline btn-sm"
                        onClick={() => onSelectProject(p.id, "bep")}
                        title="Deschide Fișa BEP"
                      >
                        Deschide
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
