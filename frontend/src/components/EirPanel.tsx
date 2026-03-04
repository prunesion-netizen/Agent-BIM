/**
 * EirPanel — Panou EIR (Exchange Information Requirements).
 */

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../contexts/AuthProvider";
import { useProject } from "../contexts/ProjectProvider";

type EirData = {
  id: number;
  eir_type: string;
  content_json: {
    information_requirements?: Array<{
      category: string;
      requirement: string;
      priority: string;
      acceptance_criteria?: string;
      responsible_discipline?: string;
    }>;
    security_requirements?: Record<string, unknown>;
    acceptance_criteria?: Record<string, unknown>;
    delivery_schedule?: Record<string, unknown>;
  };
  version: string | null;
  created_at: string;
};

export default function EirPanel() {
  const { authFetch } = useAuth();
  const { currentProject } = useProject();
  const [eir, setEir] = useState<EirData | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const projectId = currentProject?.id;

  const loadData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await authFetch(`/api/projects/${projectId}/eir`);
      if (res.ok) {
        const data = await res.json();
        setEir(data.eir || null);
      } else {
        setError(`Eroare la incarcarea EIR: HTTP ${res.status}`);
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
      const res = await authFetch(`/api/projects/${projectId}/generate-eir`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        if (data.error) {
          setError(data.error);
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

  const PRIORITY_COLORS: Record<string, string> = {
    high: "#ef4444",
    medium: "#f59e0b",
    low: "#16a34a",
  };

  const requirements = eir?.content_json?.information_requirements || [];

  return (
    <div className="demo-container">
      <header className="demo-header">
        <div className="demo-brand">
          <div className="demo-logo">&#9888;</div>
          <div>
            <h1>Cerinte Informare (EIR)</h1>
            <p className="demo-subtitle">ISO 19650-2 — Exchange Information Requirements</p>
          </div>
        </div>
        <button
          className="btn-primary"
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating ? "Se genereaza..." : "Genereaza EIR"}
        </button>
      </header>

      {error && (
        <div style={{ margin: "16px 0", padding: "12px 16px", background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 8, color: "#dc2626" }}>
          <strong>Eroare:</strong> {error}
        </div>
      )}

      {loading && <p style={{ textAlign: "center", color: "var(--gray-500)" }}>Se incarca...</p>}

      {eir && requirements.length > 0 && (
        <div className="dashboard-table-wrap">
          <table className="dashboard-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Categorie</th>
                <th>Cerinta</th>
                <th>Prioritate</th>
                <th>Criteriu Acceptare</th>
                <th>Disciplina</th>
              </tr>
            </thead>
            <tbody>
              {requirements.map((req, idx) => (
                <tr key={idx}>
                  <td>{idx + 1}</td>
                  <td><strong>{req.category}</strong></td>
                  <td>{req.requirement}</td>
                  <td>
                    <span
                      className="cde-badge"
                      style={{
                        background: PRIORITY_COLORS[req.priority] || "#9ca3af",
                        color: "#fff",
                      }}
                    >
                      {req.priority}
                    </span>
                  </td>
                  <td>{req.acceptance_criteria || "—"}</td>
                  <td>{req.responsible_discipline || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!eir && !loading && (
        <p style={{ textAlign: "center", marginTop: 32, color: "var(--gray-500)" }}>
          Nu exista EIR generat. Apasa "Genereaza EIR" pentru a crea cerintele de informare.
        </p>
      )}
    </div>
  );
}
