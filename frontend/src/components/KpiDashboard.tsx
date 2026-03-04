/**
 * KpiDashboard — Carduri KPI cu scor overall.
 */

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../contexts/AuthProvider";
import { useProject } from "../contexts/ProjectProvider";

type KpiItem = {
  name: string;
  category: string;
  value: number;
  target: number;
};

type KpiData = {
  project_id: number;
  kpis: KpiItem[];
  categories: string[];
  overall_score: number;
  measurement_date?: string;
};

const KPI_LABELS: Record<string, string> = {
  bep_compliance: "Completitudine BEP",
  delivery_on_time: "Livrare la Termen",
  clash_resolution_rate: "Rezolvare Clash-uri",
  model_completeness: "Completitudine Model",
  verification_score: "Scor Verificare",
};

const KPI_ICONS: Record<string, string> = {
  bep_compliance: "&#9776;",
  delivery_on_time: "&#9200;",
  clash_resolution_rate: "&#9888;",
  model_completeness: "&#9635;",
  verification_score: "&#9989;",
};

export default function KpiDashboard() {
  const { authFetch } = useAuth();
  const { currentProject } = useProject();
  const [data, setData] = useState<KpiData | null>(null);
  const [loading, setLoading] = useState(false);

  const projectId = currentProject?.id;

  const loadData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const res = await authFetch(`/api/projects/${projectId}/kpis`);
      if (res.ok) setData(await res.json());
    } finally {
      setLoading(false);
    }
  }, [authFetch, projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (!projectId) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">&#9733;</div>
        <div className="empty-state-title">Niciun proiect selectat</div>
        <div className="empty-state-text">Selecteaza un proiect din bara de sus.</div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="loading-center" style={{ minHeight: 200 }}>
        <div className="spinner spinner-dark spinner-lg" />
        <span>Se calculeaza KPI...</span>
      </div>
    );
  }

  if (!data) return null;

  const getColor = (value: number) => {
    if (value >= 80) return "health-green";
    if (value >= 50) return "health-yellow";
    return "health-red";
  };

  return (
    <div className="demo-container">
      <header className="demo-header">
        <div className="demo-brand">
          <div className="demo-logo">&#9733;</div>
          <div>
            <h1>KPI Dashboard</h1>
            <p className="demo-subtitle">Indicatori cheie performanta BIM</p>
          </div>
        </div>
        <button className="btn-outline btn-loading" onClick={loadData}>
          &#8635; Recalculeaza
        </button>
      </header>

      {/* Overall score */}
      <div className="compliance-overall" style={{ marginBottom: 24 }}>
        <div className={`compliance-overall-score ${getColor(data.overall_score)}`}>
          {data.overall_score}%
        </div>
        <div style={{ color: "var(--gray-500)", fontSize: 13 }}>Scor Overall</div>
      </div>

      {/* KPI cards */}
      <div className="kpi-cards-grid">
        {data.kpis.map((kpi) => (
          <div key={kpi.name} className="kpi-card">
            <div className="kpi-card-header">
              <span
                className="kpi-card-icon"
                dangerouslySetInnerHTML={{ __html: KPI_ICONS[kpi.name] || "&#9632;" }}
              />
              <span className="kpi-card-title">{KPI_LABELS[kpi.name] || kpi.name}</span>
            </div>
            <div className={`kpi-card-value ${getColor(kpi.value)}`}>
              {kpi.value}%
            </div>
            <div className="dashboard-health-bar-track" style={{ height: 6 }}>
              <div
                className={`dashboard-health-bar-fill ${getColor(kpi.value)}`}
                style={{ width: `${kpi.value}%` }}
              />
            </div>
            <div className="kpi-card-target">
              Target: {kpi.target}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
