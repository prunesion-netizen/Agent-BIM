/**
 * LoinMatrix — Tabel LOIN (Level of Information Need) per element × phase.
 */

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../contexts/AuthProvider";
import { useProject } from "../contexts/ProjectProvider";

type LoinEntry = {
  id: number;
  element_type: string;
  discipline: string;
  phase: string;
  detail_level: string | null;
  dimensionality: string | null;
  information_content: string | null;
};

type LoinData = {
  project_id: number;
  entries: LoinEntry[];
  element_types: string[];
  phases: string[];
  total_entries: number;
};

export default function LoinMatrix() {
  const { authFetch } = useAuth();
  const { currentProject } = useProject();
  const [data, setData] = useState<LoinData | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const projectId = currentProject?.id;

  const loadData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await authFetch(`/api/projects/${projectId}/loin`);
      if (res.ok) {
        setData(await res.json());
      } else {
        setError(`Eroare la incarcarea LOIN: HTTP ${res.status}`);
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
      const res = await authFetch(`/api/projects/${projectId}/generate-loin`, {
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

  return (
    <div className="demo-container">
      <header className="demo-header">
        <div className="demo-brand">
          <div className="demo-logo">&#9878;</div>
          <div>
            <h1>LOIN — Level of Information Need</h1>
            <p className="demo-subtitle">BS EN 17412-1 — Nivel detaliu per element</p>
          </div>
        </div>
        <button
          className="btn-primary"
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating ? "Se genereaza..." : "Genereaza LOIN"}
        </button>
      </header>

      {error && (
        <div style={{ margin: "16px 0", padding: "12px 16px", background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 8, color: "#dc2626" }}>
          <strong>Eroare:</strong> {error}
        </div>
      )}

      {loading && <p style={{ textAlign: "center", color: "var(--gray-500)" }}>Se incarca...</p>}

      {data && data.entries.length > 0 && (
        <div className="dashboard-table-wrap">
          <table className="dashboard-table">
            <thead>
              <tr>
                <th>Element IFC</th>
                <th>Disciplina</th>
                <th>Faza</th>
                <th>LOD</th>
                <th>Dim.</th>
                <th>Continut Informational</th>
              </tr>
            </thead>
            <tbody>
              {data.entries.map((e) => (
                <tr key={e.id}>
                  <td><strong>{e.element_type}</strong></td>
                  <td>{e.discipline}</td>
                  <td>{e.phase}</td>
                  <td>
                    <span className="cde-badge cde-shared">{e.detail_level || "—"}</span>
                  </td>
                  <td>{e.dimensionality || "—"}</td>
                  <td style={{ maxWidth: 300, fontSize: 12 }}>
                    {e.information_content || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && data.total_entries === 0 && (
        <p style={{ textAlign: "center", marginTop: 32, color: "var(--gray-500)" }}>
          Nu exista LOIN definit. Apasa "Genereaza LOIN" pentru a crea matricea.
        </p>
      )}
    </div>
  );
}
