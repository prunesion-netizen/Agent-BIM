/**
 * HandoverChecklist — Checklist predare as-built (ISO 19650-3).
 */

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../contexts/AuthProvider";
import { useProject } from "../contexts/ProjectProvider";

type HandoverItem = {
  id: number;
  item_name: string;
  category: string;
  is_completed: boolean;
  completed_by: string | null;
  completed_at: string | null;
};

type HandoverData = {
  total_items: number;
  completed_items: number;
  completion_percent: number;
  by_category: Record<string, { total: number; completed: number }>;
  items: HandoverItem[];
};

const CATEGORY_LABELS: Record<string, string> = {
  modele_as_built: "Modele As-Built",
  documentatie: "Documentatie",
  date_operare: "Date Operare",
  clasificare_spatii: "Clasificare Spatii",
  sisteme_mep: "Sisteme MEP",
  coordonare_finala: "Coordonare Finala",
};

export default function HandoverChecklist() {
  const { authFetch } = useAuth();
  const { currentProject } = useProject();
  const [data, setData] = useState<HandoverData | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const projectId = currentProject?.id;

  const loadData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await authFetch(`/api/projects/${projectId}/handover`);
      if (res.ok) {
        setData(await res.json());
      } else {
        setError(`Eroare la incarcarea Handover: HTTP ${res.status}`);
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
      const res = await authFetch(`/api/projects/${projectId}/generate-handover`, {
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

  const handleToggle = async (itemId: number) => {
    const res = await authFetch(`/api/handover-items/${itemId}/toggle`, {
      method: "POST",
    });
    if (res.ok) await loadData();
  };

  if (!projectId) {
    return <p style={{ padding: 20, color: "var(--gray-500)" }}>Selecteaza un proiect.</p>;
  }

  // Group items by category
  const grouped: Record<string, HandoverItem[]> = {};
  for (const item of data?.items || []) {
    if (!grouped[item.category]) grouped[item.category] = [];
    grouped[item.category].push(item);
  }

  return (
    <div className="demo-container">
      <header className="demo-header">
        <div className="demo-brand">
          <div className="demo-logo">&#9745;</div>
          <div>
            <h1>Handover Checklist</h1>
            <p className="demo-subtitle">ISO 19650-3 — Predare as-built</p>
          </div>
        </div>
        <button
          className="btn-primary"
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating ? "Se genereaza..." : "Genereaza Checklist"}
        </button>
      </header>

      {error && (
        <div style={{ margin: "16px 0", padding: "12px 16px", background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 8, color: "#dc2626" }}>
          <strong>Eroare:</strong> {error}
        </div>
      )}

      {loading && <p style={{ textAlign: "center", color: "var(--gray-500)" }}>Se incarca...</p>}

      {data && data.total_items > 0 && (
        <>
          {/* Progress */}
          <div className="tidp-progress-section">
            <div className="tidp-progress-info">
              <span>{data.completed_items} / {data.total_items} completate</span>
              <span className="tidp-progress-pct">{data.completion_percent}%</span>
            </div>
            <div className="dashboard-health-bar-track" style={{ height: 8 }}>
              <div
                className={`dashboard-health-bar-fill ${data.completion_percent >= 80 ? "health-green" : data.completion_percent >= 50 ? "health-yellow" : "health-red"}`}
                style={{ width: `${data.completion_percent}%` }}
              />
            </div>
          </div>

          {/* Items grouped by category */}
          {Object.entries(grouped).map(([category, items]) => (
            <div key={category} className="handover-category">
              <h3 className="handover-category-title">
                {CATEGORY_LABELS[category] || category}
                <span className="handover-category-count">
                  {items.filter((i) => i.is_completed).length}/{items.length}
                </span>
              </h3>
              <div className="handover-items">
                {items.map((item) => (
                  <label key={item.id} className={`handover-item ${item.is_completed ? "completed" : ""}`}>
                    <input
                      type="checkbox"
                      checked={item.is_completed}
                      onChange={() => handleToggle(item.id)}
                    />
                    <span>{item.item_name}</span>
                    {item.completed_by && (
                      <span className="handover-completed-by">({item.completed_by})</span>
                    )}
                  </label>
                ))}
              </div>
            </div>
          ))}
        </>
      )}

      {data && data.total_items === 0 && (
        <p style={{ textAlign: "center", marginTop: 32, color: "var(--gray-500)" }}>
          Nu exista checklist. Apasa "Genereaza Checklist" pentru a crea lista de predare.
        </p>
      )}
    </div>
  );
}
