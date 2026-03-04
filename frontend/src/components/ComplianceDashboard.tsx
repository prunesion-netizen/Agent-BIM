/**
 * ComplianceDashboard — Radar conformitate ISO 19650 per part, checklist, export.
 */

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../contexts/AuthProvider";
import { useProject } from "../contexts/ProjectProvider";

type ComplianceCheck = {
  check: string;
  status: "pass" | "warning" | "fail";
};

type CompliancePart = {
  title: string;
  score: number;
  checks: ComplianceCheck[];
};

type ComplianceData = {
  project_id: number;
  project_name: string;
  overall_score: number;
  parts: Record<string, CompliancePart>;
  recommendations: string[];
  total_checks: number;
  pass_count: number;
  warning_count: number;
  fail_count: number;
};

const CHECK_ICONS: Record<string, string> = {
  pass: "\u2705",
  warning: "\u26A0\uFE0F",
  fail: "\u274C",
};

function ScoreBar({ score, label }: { score: number; label: string }) {
  const color = score >= 80 ? "health-green" : score >= 50 ? "health-yellow" : "health-red";
  return (
    <div className="compliance-score-bar">
      <div className="compliance-score-label">
        <span>{label}</span>
        <span className={`compliance-score-value ${color}`}>{score}%</span>
      </div>
      <div className="dashboard-health-bar-track" style={{ height: 10 }}>
        <div
          className={`dashboard-health-bar-fill ${color}`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}

export default function ComplianceDashboard() {
  const { authFetch } = useAuth();
  const { currentProject } = useProject();
  const [data, setData] = useState<ComplianceData | null>(null);
  const [loading, setLoading] = useState(false);

  const projectId = currentProject?.id;

  const loadData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const res = await authFetch(`/api/projects/${projectId}/iso-compliance`);
      if (res.ok) setData(await res.json());
    } finally {
      setLoading(false);
    }
  }, [authFetch, projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (!projectId) {
    return <p style={{ padding: 20, color: "var(--gray-500)" }}>Selecteaza un proiect.</p>;
  }

  if (loading) {
    return <p style={{ padding: 40, textAlign: "center", color: "var(--gray-500)" }}>Se verifica conformitatea...</p>;
  }

  if (!data) return null;

  const overallColor = data.overall_score >= 80 ? "health-green"
    : data.overall_score >= 50 ? "health-yellow" : "health-red";

  return (
    <div className="demo-container">
      <header className="demo-header">
        <div className="demo-brand">
          <div className="demo-logo">&#9989;</div>
          <div>
            <h1>Conformitate ISO 19650</h1>
            <p className="demo-subtitle">Verificare completa parts 1/2/3/5</p>
          </div>
        </div>
        <button className="btn-outline" onClick={loadData}>
          &#8635; Reverifica
        </button>
      </header>

      {/* Overall score */}
      <div className="compliance-overall">
        <div className={`compliance-overall-score ${overallColor}`}>
          {data.overall_score}%
        </div>
        <div className="compliance-overall-details">
          <span className="compliance-stat-pass">{data.pass_count} pass</span>
          <span className="compliance-stat-warn">{data.warning_count} warning</span>
          <span className="compliance-stat-fail">{data.fail_count} fail</span>
        </div>
      </div>

      {/* Per-part scores */}
      <div className="compliance-parts">
        {Object.entries(data.parts).map(([key, part]) => (
          <div key={key} className="compliance-part-card">
            <ScoreBar score={part.score} label={part.title} />
            <div className="compliance-checks">
              {part.checks.map((check, idx) => (
                <div key={idx} className={`compliance-check compliance-check-${check.status}`}>
                  <span className="compliance-check-icon">{CHECK_ICONS[check.status]}</span>
                  <span>{check.check}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Recommendations */}
      {data.recommendations.length > 0 && (
        <div className="compliance-recommendations">
          <h3>Recomandari</h3>
          <ul>
            {data.recommendations.map((rec, idx) => (
              <li key={idx}>{rec}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
