/**
 * CobieValidator — Upload COBie XLSX, validare, rezultate, template download, istoric.
 */

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../contexts/AuthProvider";
import { useProject } from "../contexts/ProjectProvider";

type SheetCheck = {
  sheet_name: string;
  status: "pass" | "warning" | "fail" | "missing";
  row_count: number;
  missing_columns: string[];
  details: string;
};

type ProjectCheck = {
  id: string;
  label: string;
  status: "pass" | "warning" | "fail";
  details: string;
};

type ValidationResult = {
  score: number;
  overall_status: "pass" | "warning" | "fail";
  total_checks: number;
  pass_count: number;
  warning_count: number;
  fail_count: number;
  sheet_checks: SheetCheck[];
  project_checks: ProjectCheck[];
  recommendations: string[];
};

type HistoryItem = {
  id: number;
  filename: string;
  validation_type: string;
  overall_status: string;
  score: number;
  total_checks: number;
  pass_count: number;
  warning_count: number;
  fail_count: number;
  created_at: string | null;
};

const STATUS_ICONS: Record<string, string> = {
  pass: "\u2705",
  warning: "\u26A0\uFE0F",
  fail: "\u274C",
  missing: "\u2753",
};

const STATUS_CLASSES: Record<string, string> = {
  pass: "health-green",
  warning: "health-yellow",
  fail: "health-red",
  missing: "health-red",
};

export default function CobieValidator() {
  const { authFetch } = useAuth();
  const { currentProject } = useProject();
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const projectId = currentProject?.id;

  const loadHistory = useCallback(async () => {
    if (!projectId) return;
    try {
      const res = await authFetch(`/api/projects/${projectId}/cobie-validations`);
      if (res.ok) setHistory(await res.json());
    } catch {
      /* ignore */
    }
  }, [authFetch, projectId]);

  const loadLatest = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const res = await authFetch(`/api/projects/${projectId}/cobie-latest`);
      if (res.ok) {
        const data = await res.json();
        if (data.results_json) {
          setResult(data.results_json);
        }
      }
    } finally {
      setLoading(false);
    }
  }, [authFetch, projectId]);

  useEffect(() => {
    loadLatest();
    loadHistory();
  }, [loadLatest, loadHistory]);

  const handleUpload = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      if (!projectId || !e.target.files?.[0]) return;
      const file = e.target.files[0];
      if (!file.name.toLowerCase().endsWith(".xlsx")) {
        setError("Doar fisiere .xlsx sunt acceptate.");
        return;
      }

      setUploading(true);
      setError(null);
      setResult(null);

      const form = new FormData();
      form.append("file", file);

      try {
        const res = await authFetch(
          `/api/projects/${projectId}/validate-cobie`,
          { method: "POST", body: form }
        );
        if (res.ok) {
          const data: ValidationResult = await res.json();
          setResult(data);
          loadHistory();
        } else {
          const err = await res.json().catch(() => null);
          setError(err?.detail || "Eroare la validare.");
        }
      } catch (err) {
        setError("Eroare de rețea.");
      } finally {
        setUploading(false);
        e.target.value = "";
      }
    },
    [authFetch, projectId, loadHistory]
  );

  const handleDownloadTemplate = useCallback(async () => {
    if (!projectId) return;
    try {
      const res = await authFetch(
        `/api/projects/${projectId}/generate-cobie-template`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        }
      );
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `COBie_Template_${projectId}.xlsx`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch {
      /* ignore */
    }
  }, [authFetch, projectId]);

  if (!projectId) {
    return (
      <div className="compliance-container">
        <p>Selecteaza un proiect pentru validare COBie.</p>
      </div>
    );
  }

  return (
    <div className="compliance-container">
      {/* Header */}
      <div className="compliance-header">
        <h2>COBie Validator</h2>
        <p style={{ color: "#64748b", margin: "4px 0 0" }}>
          Validare Construction Operations Building information exchange (COBie)
        </p>
      </div>

      {/* Actions */}
      <div style={{ display: "flex", gap: 12, margin: "16px 0" }}>
        <label
          className="bep-export-btn"
          style={{
            cursor: uploading ? "not-allowed" : "pointer",
            opacity: uploading ? 0.6 : 1,
          }}
        >
          {uploading ? "Se valideaza..." : "Upload COBie XLSX"}
          <input
            type="file"
            accept=".xlsx"
            style={{ display: "none" }}
            onChange={handleUpload}
            disabled={uploading}
          />
        </label>

        <button
          className="bep-export-btn"
          style={{ background: "#2563eb" }}
          onClick={handleDownloadTemplate}
        >
          Genereaza Template
        </button>
      </div>

      {/* Error */}
      {error && (
        <div
          style={{
            background: "#fef2f2",
            border: "1px solid #fca5a5",
            borderRadius: 8,
            padding: "12px 16px",
            color: "#991b1b",
            marginBottom: 16,
          }}
        >
          {error}
        </div>
      )}

      {/* Loading */}
      {(loading || uploading) && (
        <div style={{ textAlign: "center", padding: 24, color: "#64748b" }}>
          Se incarca...
        </div>
      )}

      {/* Results */}
      {result && !uploading && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Score bar */}
          <div className="compliance-score-bar">
            <div className="compliance-score-label">
              <span>Scor COBie Overall</span>
              <span
                className={`compliance-score-value ${STATUS_CLASSES[result.overall_status]}`}
              >
                {result.score}%
              </span>
            </div>
            <div className="dashboard-health-bar-track" style={{ height: 12 }}>
              <div
                className={`dashboard-health-bar-fill ${STATUS_CLASSES[result.overall_status]}`}
                style={{ width: `${result.score}%` }}
              />
            </div>
          </div>

          {/* Summary counts */}
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
            <div className="kpi-card" style={{ flex: 1, minWidth: 120 }}>
              <div className="kpi-card-value health-green">{result.pass_count}</div>
              <div className="kpi-card-label">Pass</div>
            </div>
            <div className="kpi-card" style={{ flex: 1, minWidth: 120 }}>
              <div className="kpi-card-value health-yellow">
                {result.warning_count}
              </div>
              <div className="kpi-card-label">Warning</div>
            </div>
            <div className="kpi-card" style={{ flex: 1, minWidth: 120 }}>
              <div className="kpi-card-value health-red">{result.fail_count}</div>
              <div className="kpi-card-label">Fail</div>
            </div>
          </div>

          {/* Sheet checks table */}
          <div>
            <h3 style={{ margin: "0 0 8px" }}>Verificare Sheet-uri COBie</h3>
            <table className="raci-table" style={{ width: "100%" }}>
              <thead>
                <tr>
                  <th>Sheet</th>
                  <th>Status</th>
                  <th>Randuri</th>
                  <th>Coloane lipsa</th>
                  <th>Detalii</th>
                </tr>
              </thead>
              <tbody>
                {result.sheet_checks.map((sc) => (
                  <tr key={sc.sheet_name}>
                    <td style={{ fontWeight: 600 }}>{sc.sheet_name}</td>
                    <td>
                      <span className={`cde-badge cde-badge-${sc.status === "pass" ? "published" : sc.status === "warning" ? "shared" : "wip"}`}>
                        {STATUS_ICONS[sc.status]} {sc.status.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ textAlign: "center" }}>{sc.row_count}</td>
                    <td>
                      {sc.missing_columns.length > 0
                        ? sc.missing_columns.join(", ")
                        : "-"}
                    </td>
                    <td style={{ color: "#64748b", fontSize: 13 }}>
                      {sc.details}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Project checks */}
          {result.project_checks.length > 0 && (
            <div>
              <h3 style={{ margin: "0 0 8px" }}>Verificari Project-Specific</h3>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {result.project_checks.map((pc) => (
                  <div
                    key={pc.id}
                    style={{
                      background:
                        pc.status === "pass"
                          ? "#f0fdf4"
                          : pc.status === "warning"
                          ? "#fffbeb"
                          : "#fef2f2",
                      border: `1px solid ${
                        pc.status === "pass"
                          ? "#86efac"
                          : pc.status === "warning"
                          ? "#fcd34d"
                          : "#fca5a5"
                      }`,
                      borderRadius: 8,
                      padding: "10px 14px",
                    }}
                  >
                    <div style={{ fontWeight: 600 }}>
                      {STATUS_ICONS[pc.status]} {pc.label}
                    </div>
                    <div style={{ color: "#64748b", fontSize: 13, marginTop: 2 }}>
                      {pc.details}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations.length > 0 && (
            <div>
              <h3 style={{ margin: "0 0 8px" }}>Recomandari</h3>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {result.recommendations.map((r, i) => (
                  <li key={i} style={{ marginBottom: 4, color: "#475569" }}>
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h3 style={{ margin: "0 0 8px" }}>Istoric Validari COBie</h3>
          <table className="raci-table" style={{ width: "100%" }}>
            <thead>
              <tr>
                <th>Fisier</th>
                <th>Status</th>
                <th>Scor</th>
                <th>Pass / Warn / Fail</th>
                <th>Data</th>
              </tr>
            </thead>
            <tbody>
              {history.map((h) => (
                <tr key={h.id}>
                  <td>{h.filename}</td>
                  <td>
                    <span className={`cde-badge cde-badge-${h.overall_status === "pass" ? "published" : h.overall_status === "warning" ? "shared" : "wip"}`}>
                      {STATUS_ICONS[h.overall_status] || ""}{" "}
                      {h.overall_status.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ textAlign: "center" }}>{h.score}%</td>
                  <td style={{ textAlign: "center" }}>
                    {h.pass_count} / {h.warning_count} / {h.fail_count}
                  </td>
                  <td style={{ color: "#64748b", fontSize: 13 }}>
                    {h.created_at
                      ? new Date(h.created_at).toLocaleDateString("ro-RO", {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
