/**
 * LoinMatrix — Tabel LOIN (Level of Information Need) per element × phase.
 */

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../contexts/AuthProvider";
import { useProject } from "../contexts/ProjectProvider";
import { useToast } from "./Toast";

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
  const toast = useToast();
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
          toast.error("Eroare la generarea LOIN.");
        } else {
          toast.success(`LOIN generat: ${result.entries_count} intrari!`);
          await loadData();
        }
      } else {
        setError(`Eroare HTTP ${res.status}`);
        toast.error(`Eroare HTTP ${res.status}`);
      }
    } catch (e: any) {
      setError(e.message || "Eroare necunoscuta");
      toast.error("Eroare de retea la generarea LOIN.");
    } finally {
      setGenerating(false);
    }
  };

  if (!projectId) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">&#9878;</div>
        <div className="empty-state-title">Niciun proiect selectat</div>
        <div className="empty-state-text">Selecteaza un proiect din bara de sus.</div>
      </div>
    );
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
          className="btn-primary btn-loading"
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating && <span className="spinner" />}
          {generating ? "Se genereaza..." : "Genereaza LOIN"}
        </button>
      </header>

      {error && (
        <div className="alert alert-error">
          <strong>Eroare:</strong> {error}
          <button className="alert-dismiss" onClick={() => setError(null)} aria-label="Inchide eroarea">&times;</button>
        </div>
      )}

      {loading && (
        <div className="loading-center">
          <div className="spinner spinner-dark spinner-lg" />
          <span>Se incarca LOIN...</span>
        </div>
      )}

      {data && data.entries.length > 0 && (
        <div className="table-responsive">
          <table className="dashboard-table">
            <thead>
              <tr>
                <th scope="col">Element IFC</th>
                <th scope="col">Disciplina</th>
                <th scope="col">Faza</th>
                <th scope="col">LOD</th>
                <th scope="col">Dim.</th>
                <th scope="col">Continut Informational</th>
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
        <div className="empty-state">
          <div className="empty-state-icon">&#128208;</div>
          <div className="empty-state-title">Nu exista LOIN definit</div>
          <div className="empty-state-text">Apasa "Genereaza LOIN" pentru a crea matricea de nivel informational.</div>
        </div>
      )}
    </div>
  );
}
