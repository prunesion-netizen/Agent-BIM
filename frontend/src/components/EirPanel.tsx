/**
 * EirPanel — Panou EIR (Exchange Information Requirements).
 */

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../contexts/AuthProvider";
import { useProject } from "../contexts/ProjectProvider";
import { useToast } from "./Toast";

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
  const toast = useToast();
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
          toast.error("Eroare la generarea EIR.");
        } else {
          toast.success("EIR generat cu succes!");
          await loadData();
        }
      } else {
        setError(`Eroare HTTP ${res.status}`);
        toast.error(`Eroare HTTP ${res.status}`);
      }
    } catch (e: any) {
      setError(e.message || "Eroare necunoscuta");
      toast.error("Eroare de retea la generarea EIR.");
    } finally {
      setGenerating(false);
    }
  };

  if (!projectId) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">&#9888;</div>
        <div className="empty-state-title">Niciun proiect selectat</div>
        <div className="empty-state-text">Selecteaza un proiect din bara de sus pentru a vedea EIR.</div>
      </div>
    );
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
          className="btn-primary btn-loading"
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating && <span className="spinner" />}
          {generating ? "Se genereaza..." : "Genereaza EIR"}
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
          <span>Se incarca EIR...</span>
        </div>
      )}

      {eir && requirements.length > 0 && (
        <div className="table-responsive">
          <table className="dashboard-table">
            <thead>
              <tr>
                <th scope="col">#</th>
                <th scope="col">Categorie</th>
                <th scope="col">Cerinta</th>
                <th scope="col">Prioritate</th>
                <th scope="col">Criteriu Acceptare</th>
                <th scope="col">Disciplina</th>
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
        <div className="empty-state">
          <div className="empty-state-icon">&#128196;</div>
          <div className="empty-state-title">Nu exista EIR generat</div>
          <div className="empty-state-text">Apasa "Genereaza EIR" pentru a crea cerintele de informare conform ISO 19650-2.</div>
        </div>
      )}
    </div>
  );
}
