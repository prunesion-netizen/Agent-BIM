/**
 * ToolCallCard.tsx — Card vizual pentru un tool call al agentului.
 *
 * Afișează: spinner (running), rezultat (completed), detalii colapsabile.
 * Vizualizare specializată per tool type.
 */

import { useState } from "react";
import type { ToolStep } from "../types/agent";
import { TOOL_LABELS } from "../types/agent";

interface Props {
  step: ToolStep;
}

/** Iconiță per tool */
const TOOL_ICONS: Record<string, string> = {
  generate_bep: "📄",
  verify_bep: "🔍",
  export_bep_docx: "📥",
  search_bim_standards: "📚",
  analyze_ifc_model: "🏗️",
  list_document_versions: "📋",
  compare_bep_versions: "🔀",
  get_audit_trail: "📜",
  get_project_health_check: "💊",
};

function SpecializedResult({ step }: { step: ToolStep }) {
  const r = step.result || {};
  const toolName = step.tool_name;

  // generate_bep → banner verde cu versiune
  if (toolName === "generate_bep" && r.success) {
    return (
      <div className="tool-specialized tool-specialized--success">
        <span className="tool-specialized-badge">BEP {r.bep_version as string}</span>
        <span>generat cu succes ({((r.bep_length as number) / 1000).toFixed(1)}K caractere)</span>
      </div>
    );
  }

  // verify_bep → mini bară pass/warning/fail
  if (toolName === "verify_bep" && r.summary) {
    const summary = r.summary as Record<string, unknown>;
    const status = summary.overall_status as string;
    const statusClass =
      status === "pass" ? "pass" : status === "fail" ? "fail" : "warning";
    return (
      <div className={`tool-specialized tool-specialized--verify tool-specialized--${statusClass}`}>
        <span className={`tool-verify-status tool-verify-status--${statusClass}`}>
          {status === "pass" ? "✓ PASS" : status === "fail" ? "✗ FAIL" : "⚠ WARNING"}
        </span>
        {summary.fail_count ? (
          <span className="tool-verify-count tool-verify-count--fail">
            {summary.fail_count as number} neconformități
          </span>
        ) : null}
        {summary.warning_count ? (
          <span className="tool-verify-count tool-verify-count--warning">
            {summary.warning_count as number} avertismente
          </span>
        ) : null}
      </div>
    );
  }

  // export_bep_docx → buton download
  if (toolName === "export_bep_docx" && r.download_url) {
    return (
      <div className="tool-specialized tool-specialized--download">
        <a
          href={r.download_url as string}
          target="_blank"
          rel="noopener noreferrer"
          className="tool-download-btn"
        >
          📥 Descarcă {r.filename as string || "BEP.docx"}
        </a>
      </div>
    );
  }

  // search_bim_standards → carduri compacte
  if (toolName === "search_bim_standards" && r.results) {
    const results = r.results as Array<Record<string, unknown>>;
    if (results.length === 0) return null;
    return (
      <div className="tool-specialized tool-specialized--search">
        <span className="tool-search-count">{results.length} rezultate găsite</span>
        {results.slice(0, 3).map((res, i) => (
          <div key={i} className="tool-search-item">
            <span className="tool-search-source">{(res.source as string) || "Standard"}</span>
            <span className="tool-search-text">
              {((res.text as string) || "").slice(0, 120)}
              {((res.text as string) || "").length > 120 ? "…" : ""}
            </span>
          </div>
        ))}
      </div>
    );
  }

  // analyze_ifc_model → tabel categorii + pills discipline
  if (toolName === "analyze_ifc_model" && r.analysis) {
    const analysis = r.analysis as Record<string, unknown>;
    const disciplines = (analysis.disciplines_detected as string[]) || [];
    const categories = (analysis.categories as Array<Record<string, unknown>>) || [];
    const issues = (analysis.potential_issues as string[]) || [];
    return (
      <div className="tool-specialized tool-specialized--ifc">
        <div className="tool-ifc-header">
          <span className="tool-ifc-filename">{analysis.filename as string}</span>
          <span className="tool-ifc-size">{analysis.file_size_mb as number} MB</span>
          <span className="tool-ifc-elements">{analysis.total_elements as number} elemente</span>
        </div>
        {disciplines.length > 0 && (
          <div className="tool-ifc-disciplines">
            {disciplines.map((d) => (
              <span key={d} className="tool-ifc-pill">{d}</span>
            ))}
          </div>
        )}
        {categories.length > 0 && (
          <div className="tool-ifc-categories">
            {categories.slice(0, 6).map((c, i) => (
              <div key={i} className="tool-ifc-cat-row">
                <span className="tool-ifc-cat-name">{c.name as string}</span>
                <span className="tool-ifc-cat-count">{c.element_count as number}</span>
              </div>
            ))}
          </div>
        )}
        {issues.length > 0 && (
          <div className="tool-ifc-issues">
            {issues.map((issue, i) => (
              <div key={i} className="tool-ifc-issue">⚠ {issue}</div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // get_project_health_check → scor + alerte
  if (toolName === "get_project_health_check" && r.score != null) {
    const score = r.score as number;
    const alerts = (r.alerts as string[]) || [];
    const recommendations = (r.recommendations as string[]) || [];
    const scoreClass = score >= 80 ? "pass" : score >= 50 ? "warning" : "fail";
    return (
      <div className="tool-specialized tool-specialized--health">
        <div className={`tool-health-score tool-health-score--${scoreClass}`}>
          <span className="tool-health-score-value">{score}%</span>
          <span className="tool-health-score-label">completitudine</span>
        </div>
        <div className="tool-health-flags">
          <span className={r.has_bep ? "tool-health-flag--ok" : "tool-health-flag--missing"}>
            {r.has_bep ? "✓" : "✗"} BEP
          </span>
          <span className={r.has_ifc ? "tool-health-flag--ok" : "tool-health-flag--missing"}>
            {r.has_ifc ? "✓" : "✗"} IFC
          </span>
          <span className={r.has_verification ? "tool-health-flag--ok" : "tool-health-flag--missing"}>
            {r.has_verification ? "✓" : "✗"} Verificare
          </span>
        </div>
        {alerts.length > 0 && (
          <div className="tool-health-alerts">
            {alerts.map((a, i) => (
              <div key={i} className="tool-health-alert">⚠ {a}</div>
            ))}
          </div>
        )}
        {recommendations.length > 0 && (
          <div className="tool-health-recs">
            {recommendations.slice(0, 3).map((rec, i) => (
              <div key={i} className="tool-health-rec">→ {rec}</div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // compare_bep_versions → diff summary
  if (toolName === "compare_bep_versions" && r.diff) {
    const diff = r.diff as Record<string, unknown>;
    const added = (diff.added as string[]) || [];
    const removed = (diff.removed as string[]) || [];
    const modified = (diff.modified as Array<Record<string, unknown>>) || [];
    return (
      <div className="tool-specialized tool-specialized--diff">
        <div className="tool-diff-summary">{diff.summary as string}</div>
        {added.length > 0 && (
          <div className="tool-diff-section">
            <span className="tool-diff-label tool-diff-label--added">+ Adăugate:</span>
            {added.map((s, i) => <span key={i} className="tool-diff-item">{s}</span>)}
          </div>
        )}
        {removed.length > 0 && (
          <div className="tool-diff-section">
            <span className="tool-diff-label tool-diff-label--removed">- Șterse:</span>
            {removed.map((s, i) => <span key={i} className="tool-diff-item">{s}</span>)}
          </div>
        )}
        {modified.length > 0 && (
          <div className="tool-diff-section">
            <span className="tool-diff-label tool-diff-label--modified">~ Modificate:</span>
            {modified.map((m, i) => (
              <span key={i} className="tool-diff-item">{m.heading as string} ({m.summary as string})</span>
            ))}
          </div>
        )}
      </div>
    );
  }

  // get_audit_trail → timeline
  if (toolName === "get_audit_trail" && r.trail) {
    const trail = (r.trail as Array<Record<string, unknown>>) || [];
    if (trail.length === 0) return null;
    return (
      <div className="tool-specialized tool-specialized--audit">
        <span className="tool-audit-count">{trail.length} activități</span>
        {trail.slice(0, 5).map((entry, i) => (
          <div key={i} className="tool-audit-entry">
            <span className="tool-audit-action">{entry.action as string}</span>
            <span className="tool-audit-actor">{entry.actor as string}</span>
            <span className="tool-audit-date">
              {entry.created_at ? new Date(entry.created_at as string).toLocaleDateString("ro-RO", {
                day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit"
              }) : ""}
            </span>
          </div>
        ))}
      </div>
    );
  }

  return null;
}

export default function ToolCallCard({ step }: Props) {
  const [expanded, setExpanded] = useState(false);

  const label = TOOL_LABELS[step.tool_name] || step.tool_name;
  const icon = TOOL_ICONS[step.tool_name] || "";
  const isRunning = step.status === "running";
  const isError = step.status === "error";
  const isCompleted = step.status === "completed";

  const statusIcon = isRunning
    ? "\u23F3" // hourglass
    : isError
      ? "\u274C" // red X
      : "\u2705"; // green check

  const hasError = step.result?.error;

  return (
    <div
      className={`tool-card ${isRunning ? "tool-card--running" : ""} ${isError ? "tool-card--error" : ""}`}
    >
      <div
        className="tool-card-header"
        onClick={() => !isRunning && setExpanded(!expanded)}
      >
        <span className="tool-card-icon">
          {isRunning ? (
            <span className="tool-card-spinner" />
          ) : (
            statusIcon
          )}
        </span>
        <span className="tool-card-label">
          {icon && <span className="tool-card-tool-icon">{icon} </span>}
          {label}
        </span>
        {step.duration_ms != null && (
          <span className="tool-card-duration">
            {step.duration_ms < 1000
              ? `${step.duration_ms}ms`
              : `${(step.duration_ms / 1000).toFixed(1)}s`}
          </span>
        )}
        {!isRunning && (
          <span className="tool-card-chevron">
            {expanded ? "\u25B2" : "\u25BC"}
          </span>
        )}
      </div>

      {/* Specialized result visualization or fallback summary */}
      {isCompleted && !hasError && !expanded && (
        <SpecializedResult step={step} />
      )}

      {isCompleted && !expanded && !hasError && !TOOL_ICONS[step.tool_name] && (
        <div className="tool-card-summary">
          {step.result?.message as string || "Executat cu succes"}
        </div>
      )}

      {isError && !expanded && (
        <div className="tool-card-summary tool-card-summary--error">
          {(step.result?.error as string) || "Eroare la execuție"}
        </div>
      )}

      {/* Expanded details */}
      {expanded && (
        <div className="tool-card-details">
          <div className="tool-card-section">
            <strong>Input:</strong>
            <pre>{JSON.stringify(step.tool_input, null, 2)}</pre>
          </div>
          {step.result && (
            <div className="tool-card-section">
              <strong>Rezultat:</strong>
              <pre>
                {JSON.stringify(step.result, null, 2).slice(0, 2000)}
                {JSON.stringify(step.result, null, 2).length > 2000 && "\n..."}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
