/**
 * ToolCallCard.tsx — Card vizual pentru un tool call al agentului.
 *
 * Afișează: spinner (running), rezultat (completed), detalii colapsabile.
 */

import { useState } from "react";
import type { ToolStep } from "../types/agent";
import { TOOL_LABELS } from "../types/agent";

interface Props {
  step: ToolStep;
}

export default function ToolCallCard({ step }: Props) {
  const [expanded, setExpanded] = useState(false);

  const label = TOOL_LABELS[step.tool_name] || step.tool_name;
  const isRunning = step.status === "running";
  const isError = step.status === "error";
  const isCompleted = step.status === "completed";

  const statusIcon = isRunning
    ? "\u23F3" // hourglass
    : isError
      ? "\u274C" // red X
      : "\u2705"; // green check

  const hasError = step.result?.error;
  const hasDownloadUrl = step.result?.download_url;

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
        <span className="tool-card-label">{label}</span>
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

      {/* Quick summary line */}
      {isCompleted && !expanded && !hasError && (
        <div className="tool-card-summary">
          {step.result?.message as string || "Executat cu succes"}
        </div>
      )}

      {isError && !expanded && (
        <div className="tool-card-summary tool-card-summary--error">
          {(step.result?.error as string) || "Eroare la execuție"}
        </div>
      )}

      {/* Download link if applicable */}
      {hasDownloadUrl && (
        <div className="tool-card-download">
          <a
            href={step.result!.download_url as string}
            target="_blank"
            rel="noopener noreferrer"
            className="tool-card-download-link"
          >
            Descarcă {step.result!.filename as string || "fișierul"}
          </a>
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
