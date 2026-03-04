/**
 * RaciMatrix — Tabel interactiv RACI (tasks × roles, celule colorate R/A/C/I).
 */

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../contexts/AuthProvider";
import { useProject } from "../contexts/ProjectProvider";

type RaciEntry = {
  id: number;
  task_name: string;
  role_code: string;
  assignment: string;
  discipline: string | null;
  phase: string | null;
};

type RaciData = {
  project_id: number;
  entries: RaciEntry[];
  tasks: string[];
  roles: string[];
  total_entries: number;
};

const ASSIGNMENT_COLORS: Record<string, { bg: string; fg: string }> = {
  R: { bg: "#dc2626", fg: "#fff" },
  A: { bg: "#2563eb", fg: "#fff" },
  C: { bg: "#f59e0b", fg: "#fff" },
  I: { bg: "#9ca3af", fg: "#fff" },
};

export default function RaciMatrix() {
  const { authFetch } = useAuth();
  const { currentProject } = useProject();
  const [data, setData] = useState<RaciData | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const projectId = currentProject?.id;

  const loadData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await authFetch(`/api/projects/${projectId}/raci`);
      if (res.ok) {
        setData(await res.json());
      } else {
        setError(`Eroare la incarcarea RACI: HTTP ${res.status}`);
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
      const res = await authFetch(`/api/projects/${projectId}/generate-raci`, {
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

  // Build matrix: tasks × roles
  const tasks = data?.tasks || [];
  const roles = data?.roles || [];
  const matrix: Record<string, Record<string, string>> = {};
  for (const entry of data?.entries || []) {
    if (!matrix[entry.task_name]) matrix[entry.task_name] = {};
    matrix[entry.task_name][entry.role_code] = entry.assignment;
  }

  return (
    <div className="demo-container">
      <header className="demo-header">
        <div className="demo-brand">
          <div className="demo-logo">&#9881;</div>
          <div>
            <h1>Matrice RACI</h1>
            <p className="demo-subtitle">ISO 19650-2 — Responsabilitati BIM</p>
          </div>
        </div>
        <button
          className="btn-primary"
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating ? "Se genereaza..." : "Genereaza RACI"}
        </button>
      </header>

      {/* Legend */}
      <div className="raci-legend">
        {Object.entries(ASSIGNMENT_COLORS).map(([key, { bg }]) => (
          <span key={key} className="raci-legend-item">
            <span className="raci-cell" style={{ background: bg, color: "#fff" }}>{key}</span>
            {key === "R" && " Responsible"}
            {key === "A" && " Accountable"}
            {key === "C" && " Consulted"}
            {key === "I" && " Informed"}
          </span>
        ))}
      </div>

      {error && (
        <div style={{ margin: "16px 0", padding: "12px 16px", background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 8, color: "#dc2626" }}>
          <strong>Eroare:</strong> {error}
        </div>
      )}

      {loading && <p style={{ textAlign: "center", color: "var(--gray-500)" }}>Se incarca...</p>}

      {data && tasks.length > 0 && roles.length > 0 && (
        <div className="dashboard-table-wrap">
          <table className="dashboard-table raci-table">
            <thead>
              <tr>
                <th>Task</th>
                {roles.map((r) => (
                  <th key={r} className="raci-role-header">{r}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => (
                <tr key={task}>
                  <td className="raci-task-cell">{task}</td>
                  {roles.map((role) => {
                    const assignment = matrix[task]?.[role];
                    const colors = assignment ? ASSIGNMENT_COLORS[assignment] : null;
                    return (
                      <td key={role} className="raci-assignment-cell">
                        {assignment && (
                          <span
                            className="raci-cell"
                            style={{
                              background: colors?.bg,
                              color: colors?.fg,
                            }}
                          >
                            {assignment}
                          </span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && data.total_entries === 0 && (
        <p style={{ textAlign: "center", marginTop: 32, color: "var(--gray-500)" }}>
          Nu exista matrice RACI. Apasa "Genereaza RACI" pentru a crea matricea de responsabilitati.
        </p>
      )}
    </div>
  );
}
