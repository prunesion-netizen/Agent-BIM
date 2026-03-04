/**
 * DeliveryPlan — Tabel livrabile TIDP/MIDP cu bară progres.
 */

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../contexts/AuthProvider";
import { useProject } from "../contexts/ProjectProvider";

type Deliverable = {
  id: number;
  title: string;
  discipline: string;
  format: string;
  lod: string | null;
  responsible_role: string | null;
  due_date: string | null;
  phase: string | null;
  status: string;
};

type DeliveryPlanData = {
  total_deliverables: number;
  by_discipline: Record<string, number>;
  by_status: Record<string, number>;
  completion_percent: number;
  overdue_count: number;
  deliverables: Deliverable[];
};

export default function DeliveryPlan() {
  const { authFetch } = useAuth();
  const { currentProject } = useProject();
  const [data, setData] = useState<DeliveryPlanData | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const projectId = currentProject?.id;

  const loadData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await authFetch(`/api/projects/${projectId}/delivery-plan`);
      if (res.ok) {
        setData(await res.json());
      } else {
        setError(`Eroare la incarcarea TIDP: HTTP ${res.status}`);
      }
    } catch (e: any) {
      setError(`Eroare retea: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, [authFetch, projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleGenerate = async () => {
    if (!projectId) return;
    setGenerating(true);
    setError(null);
    try {
      const res = await authFetch(`/api/projects/${projectId}/generate-tidp`, {
        method: "POST",
      });
      if (res.ok) {
        const result = await res.json();
        if (result.error) {
          setError(result.error);
        } else {
          await loadData();
        }
      } else {
        setError(`Eroare HTTP ${res.status}`);
      }
    } catch (e: any) {
      setError(e.message || "Eroare necunoscuta");
    } finally {
      setGenerating(false);
    }
  };

  if (!projectId) {
    return <p style={{ padding: 20, color: "var(--gray-500)" }}>Selecteaza un proiect.</p>;
  }

  const STATUS_COLORS: Record<string, string> = {
    planned: "#9ca3af",
    in_progress: "#60a5fa",
    completed: "#16a34a",
    delivered: "#059669",
  };

  return (
    <div className="demo-container">
      <header className="demo-header">
        <div className="demo-brand">
          <div className="demo-logo">&#9998;</div>
          <div>
            <h1>Plan de Livrare (TIDP/MIDP)</h1>
            <p className="demo-subtitle">ISO 19650-2 — Task Information Delivery Plan</p>
          </div>
        </div>
        <button
          className="btn-primary"
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating ? "Se genereaza..." : "Genereaza TIDP"}
        </button>
      </header>

      {error && (
        <div style={{ margin: "16px 0", padding: "12px 16px", background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 8, color: "#dc2626" }}>
          <strong>Eroare:</strong> {error}
        </div>
      )}

      {loading && <p style={{ textAlign: "center", color: "var(--gray-500)" }}>Se incarca...</p>}

      {data && data.total_deliverables > 0 && (
        <>
          {/* Progress bar */}
          <div className="tidp-progress-section">
            <div className="tidp-progress-info">
              <span>{data.total_deliverables} livrabile</span>
              <span className="tidp-progress-pct">{data.completion_percent}% completate</span>
              {data.overdue_count > 0 && (
                <span className="tidp-overdue">{data.overdue_count} intarziate</span>
              )}
            </div>
            <div className="dashboard-health-bar-track" style={{ height: 8 }}>
              <div
                className="dashboard-health-bar-fill health-green"
                style={{ width: `${data.completion_percent}%` }}
              />
            </div>
          </div>

          {/* Table */}
          <div className="dashboard-table-wrap">
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>Livrabil</th>
                  <th>Disciplina</th>
                  <th>Format</th>
                  <th>LOD</th>
                  <th>Responsabil</th>
                  <th>Deadline</th>
                  <th>Faza</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.deliverables.map((d) => (
                  <tr key={d.id}>
                    <td><strong>{d.title}</strong></td>
                    <td>{d.discipline}</td>
                    <td>{d.format}</td>
                    <td>{d.lod || "—"}</td>
                    <td>{d.responsible_role || "—"}</td>
                    <td>{d.due_date || "—"}</td>
                    <td>{d.phase || "—"}</td>
                    <td>
                      <span
                        className="cde-badge"
                        style={{
                          background: STATUS_COLORS[d.status] || "#9ca3af",
                          color: "#fff",
                        }}
                      >
                        {d.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {data && data.total_deliverables === 0 && (
        <p style={{ textAlign: "center", marginTop: 32, color: "var(--gray-500)" }}>
          Nu exista livrabile. Apasa "Genereaza TIDP" pentru a crea planul de livrare.
        </p>
      )}
    </div>
  );
}
