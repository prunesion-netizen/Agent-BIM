/**
 * ClashManager — Tabel clash-uri cu filtre severitate/status.
 */

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../contexts/AuthProvider";
import { useProject } from "../contexts/ProjectProvider";

type ClashRecord = {
  id: number;
  discipline_a: string;
  discipline_b: string;
  severity: string;
  description: string | null;
  status: string;
  assigned_to_role: string | null;
  resolution_note: string | null;
  created_at: string;
  resolved_at: string | null;
};

type ClashData = {
  total: number;
  open: number;
  resolved: number;
  by_severity: Record<string, number>;
  clashes: ClashRecord[];
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#dc2626",
  high: "#ef4444",
  medium: "#f59e0b",
  low: "#16a34a",
};

export default function ClashManager() {
  const { authFetch } = useAuth();
  const { currentProject } = useProject();
  const [data, setData] = useState<ClashData | null>(null);
  const [loading, setLoading] = useState(false);
  const [filterStatus, setFilterStatus] = useState("all");

  const projectId = currentProject?.id;

  const loadData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const res = await authFetch(`/api/projects/${projectId}/clashes`);
      if (res.ok) setData(await res.json());
    } finally {
      setLoading(false);
    }
  }, [authFetch, projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleResolve = async (clashId: number) => {
    const res = await authFetch(`/api/clashes/${clashId}/resolve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resolution_note: "Rezolvat" }),
    });
    if (res.ok) await loadData();
  };

  if (!projectId) {
    return <p style={{ padding: 20, color: "var(--gray-500)" }}>Selecteaza un proiect.</p>;
  }

  const filtered = data?.clashes.filter(
    (c) => filterStatus === "all" || c.status === filterStatus
  ) || [];

  return (
    <div className="demo-container">
      <header className="demo-header">
        <div className="demo-brand">
          <div className="demo-logo">&#9888;</div>
          <div>
            <h1>Clash Management</h1>
            <p className="demo-subtitle">Coordonare interdisciplinara</p>
          </div>
        </div>
      </header>

      {loading && <p style={{ textAlign: "center", color: "var(--gray-500)" }}>Se incarca...</p>}

      {data && (
        <>
          {/* Summary */}
          <div className="dashboard-summary-row" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
            <div className="dashboard-stat-card">
              <div className="dashboard-stat-value">{data.total}</div>
              <div className="dashboard-stat-label">Total</div>
            </div>
            <div className="dashboard-stat-card">
              <div className="dashboard-stat-value" style={{ color: "#f59e0b" }}>{data.open}</div>
              <div className="dashboard-stat-label">Deschise</div>
            </div>
            <div className="dashboard-stat-card">
              <div className="dashboard-stat-value dashboard-stat-ok">{data.resolved}</div>
              <div className="dashboard-stat-label">Rezolvate</div>
            </div>
          </div>

          {/* Filter */}
          <div className="dashboard-filters" style={{ marginTop: 16 }}>
            <select
              className="dashboard-filter-select"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="all">Toate</option>
              <option value="open">Deschise</option>
              <option value="resolved">Rezolvate</option>
            </select>
          </div>

          {filtered.length > 0 && (
            <div className="dashboard-table-wrap">
              <table className="dashboard-table">
                <thead>
                  <tr>
                    <th>Discipline</th>
                    <th>Severitate</th>
                    <th>Descriere</th>
                    <th>Status</th>
                    <th>Asignat</th>
                    <th>Actiuni</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((c) => (
                    <tr key={c.id}>
                      <td><strong>{c.discipline_a}</strong> vs <strong>{c.discipline_b}</strong></td>
                      <td>
                        <span className="cde-badge" style={{ background: SEVERITY_COLORS[c.severity] || "#9ca3af", color: "#fff" }}>
                          {c.severity}
                        </span>
                      </td>
                      <td>{c.description || "—"}</td>
                      <td>
                        <span className={`cde-badge ${c.status === "open" ? "cde-wip" : "cde-published"}`}>
                          {c.status}
                        </span>
                      </td>
                      <td>{c.assigned_to_role || "—"}</td>
                      <td>
                        {c.status === "open" && (
                          <button className="btn-outline btn-sm" onClick={() => handleResolve(c.id)}>
                            Rezolva
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {data.total === 0 && (
            <p style={{ textAlign: "center", marginTop: 32, color: "var(--gray-500)" }}>
              Nu exista clash-uri inregistrate.
            </p>
          )}
        </>
      )}
    </div>
  );
}
