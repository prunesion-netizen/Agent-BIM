/**
 * RaciMatrix — Tabel interactiv RACI (tasks × roles, celule colorate R/A/C/I).
 */

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../contexts/AuthProvider";
import { useProject } from "../contexts/ProjectProvider";
import { useToast } from "./Toast";

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
  const toast = useToast();
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
          toast.error("Eroare la generarea RACI.");
        } else {
          toast.success(`Matrice RACI generata: ${result.entries_count} intrari!`);
          await loadData();
        }
      } else {
        setError(`Eroare HTTP ${res.status}`);
        toast.error(`Eroare HTTP ${res.status}`);
      }
    } catch (e: any) {
      setError(e.message || "Eroare necunoscuta");
      toast.error("Eroare de retea la generarea RACI.");
    } finally {
      setGenerating(false);
    }
  };

  if (!projectId) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">&#9881;</div>
        <div className="empty-state-title">Niciun proiect selectat</div>
        <div className="empty-state-text">Selecteaza un proiect din bara de sus.</div>
      </div>
    );
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
          className="btn-primary btn-loading"
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating && <span className="spinner" />}
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
        <div className="alert alert-error">
          <strong>Eroare:</strong> {error}
          <button className="alert-dismiss" onClick={() => setError(null)} aria-label="Inchide eroarea">&times;</button>
        </div>
      )}

      {loading && (
        <div className="loading-center">
          <div className="spinner spinner-dark spinner-lg" />
          <span>Se incarca matricea RACI...</span>
        </div>
      )}

      {data && tasks.length > 0 && roles.length > 0 && (
        <div className="table-responsive">
          <table className="dashboard-table raci-table">
            <thead>
              <tr>
                <th scope="col">Task</th>
                {roles.map((r) => (
                  <th key={r} scope="col" className="raci-role-header">{r}</th>
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
        <div className="empty-state">
          <div className="empty-state-icon">&#128101;</div>
          <div className="empty-state-title">Nu exista matrice RACI</div>
          <div className="empty-state-text">Apasa "Genereaza RACI" pentru a crea matricea de responsabilitati.</div>
        </div>
      )}
    </div>
  );
}
