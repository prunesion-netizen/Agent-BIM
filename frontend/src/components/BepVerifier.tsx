import { useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { BepContext } from "../App";

interface Props {
  bepContext?: BepContext | null;
}

interface Check {
  id: string;
  label: string;
  status: "pass" | "warning" | "fail";
  details: string;
}

interface VerificationResult {
  report_markdown: string;
  checks: Check[];
  summary: {
    total_checks: number;
    pass_count: number;
    warning_count: number;
    fail_count: number;
    overall_status: "pass" | "warning" | "fail";
  };
}

const DISCIPLINE_OPTIONS = [
  "Arhitectura",
  "Structura",
  "Instalatii HVAC",
  "Instalatii electrice",
  "Instalatii sanitare",
  "Peisagistica",
  "Drumuri si utilitati",
];

const FORMAT_OPTIONS = ["IFC 2x3", "IFC 4", "NWD", "NWC", "RVT", "DWG"];

export default function BepVerifier({ bepContext }: Props) {
  const [disciplines, setDisciplines] = useState<string[]>([]);
  const [formats, setFormats] = useState<string[]>([]);
  const [hasGeoref, setHasGeoref] = useState(false);
  const [coordSystem, setCoordSystem] = useState("");
  const [lodInfo, setLodInfo] = useState("");
  const [elementCategories, setElementCategories] = useState("");
  const [additionalNotes, setAdditionalNotes] = useState("");

  const [result, setResult] = useState<VerificationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggleItem(list: string[], item: string, setter: (v: string[]) => void) {
    setter(list.includes(item) ? list.filter((x) => x !== item) : [...list, item]);
  }

  async function handleVerify() {
    if (!bepContext) {
      setError("Nu exista BEP generat. Genereaza mai intai un BEP din tab-ul Fisa BEP.");
      return;
    }
    if (disciplines.length === 0) {
      setError("Selecteaza cel putin o disciplina din model.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const modelSummary: Record<string, unknown> = {
      disciplines_present: disciplines,
      exchange_formats_available: formats,
      has_georeferencing: hasGeoref,
      coordinate_system: coordSystem || null,
      lod_loi_info: lodInfo || null,
      element_categories: elementCategories
        ? elementCategories.split(",").map((s) => s.trim()).filter(Boolean)
        : [],
      additional_notes: additionalNotes || null,
    };

    try {
      const res = await fetch("/api/verify-bep", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_code: bepContext.projectCode,
          model_summary: modelSummary,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(err.detail || `Eroare server: ${res.status}`);
      }

      const data: VerificationResult = await res.json();
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Eroare necunoscuta");
    } finally {
      setLoading(false);
    }
  }

  function statusIcon(status: string) {
    if (status === "pass") return "\u2705";
    if (status === "warning") return "\u26A0\uFE0F";
    return "\u274C";
  }

  function statusLabel(status: string) {
    if (status === "pass") return "Conform";
    if (status === "warning") return "Atenție";
    return "Neconform";
  }

  return (
    <div className="verifier-container">
      {/* Header */}
      <header className="verifier-header">
        <div className="demo-brand">
          <div className="demo-logo" style={{ background: "linear-gradient(135deg, #7c3aed, #4f46e5)" }}>
            QC
          </div>
          <div>
            <h1>Verificare BEP vs Model</h1>
            <p>Compara specificatiile BEP cu starea reala a modelului BIM</p>
          </div>
        </div>
      </header>

      {/* Context bar */}
      {bepContext ? (
        <div className="chat-context-bar">
          <span className="chat-context-dot" />
          BEP activ: <strong>{bepContext.projectName}</strong> ({bepContext.projectCode})
        </div>
      ) : (
        <div className="verifier-no-bep">
          Nu exista BEP generat. Mergi la tab-ul <strong>Fisa BEP</strong> si genereaza
          un BEP mai intai.
        </div>
      )}

      {/* Model Summary Form */}
      <div className="verifier-form">
        <fieldset className="pcf-section">
          <legend>Rezumat Model BIM</legend>

          <div className="pcf-field full">
            <span>Discipline prezente in model</span>
            <div className="pcf-check-row">
              {DISCIPLINE_OPTIONS.map((d) => (
                <label key={d} className="pcf-pill">
                  <input
                    type="checkbox"
                    checked={disciplines.includes(d)}
                    onChange={() => toggleItem(disciplines, d, setDisciplines)}
                  />
                  {d}
                </label>
              ))}
            </div>
          </div>

          <div className="pcf-field full" style={{ marginTop: 16 }}>
            <span>Formate de schimb disponibile</span>
            <div className="pcf-check-row">
              {FORMAT_OPTIONS.map((f) => (
                <label key={f} className="pcf-pill">
                  <input
                    type="checkbox"
                    checked={formats.includes(f)}
                    onChange={() => toggleItem(formats, f, setFormats)}
                  />
                  {f}
                </label>
              ))}
            </div>
          </div>

          <div className="pcf-grid" style={{ marginTop: 16 }}>
            <label className="pcf-field pcf-checkbox">
              <input
                type="checkbox"
                checked={hasGeoref}
                onChange={() => setHasGeoref(!hasGeoref)}
              />
              <span>Modelul are georeferentiere</span>
            </label>

            <div className="pcf-field">
              <span>Sistem de coordonate</span>
              <input
                type="text"
                value={coordSystem}
                onChange={(e) => setCoordSystem(e.target.value)}
                placeholder="ex: Stereo 70 / EPSG:31700"
              />
            </div>

            <div className="pcf-field">
              <span>Informatii LOD/LOI</span>
              <input
                type="text"
                value={lodInfo}
                onChange={(e) => setLodInfo(e.target.value)}
                placeholder="ex: LOD 300 general, LOD 350 structura"
              />
            </div>

            <div className="pcf-field">
              <span>Categorii de elemente (separate prin virgula)</span>
              <input
                type="text"
                value={elementCategories}
                onChange={(e) => setElementCategories(e.target.value)}
                placeholder="ex: Walls, Floors, Columns, Beams, Ducts"
              />
            </div>
          </div>

          <div className="pcf-field full" style={{ marginTop: 16 }}>
            <span>Observatii suplimentare</span>
            <textarea
              value={additionalNotes}
              onChange={(e) => setAdditionalNotes(e.target.value)}
              placeholder="Orice detalii suplimentare despre modelul BIM..."
              rows={3}
            />
          </div>
        </fieldset>
      </div>

      {/* Actions */}
      <div className="demo-actions">
        <button
          className="btn-primary"
          onClick={handleVerify}
          disabled={loading || !bepContext}
          style={bepContext ? { background: "linear-gradient(135deg, #7c3aed, #4f46e5)" } : undefined}
        >
          {loading ? "Se verifica..." : "Verifica conformitatea"}
        </button>
      </div>

      {/* Error */}
      {error && <div className="demo-alert error">{error}</div>}

      {/* Results */}
      {result && (
        <div className="verifier-results">
          {/* Summary bar */}
          <div className={`verifier-summary verifier-summary-${result.summary.overall_status}`}>
            <div className="verifier-summary-icon">
              {statusIcon(result.summary.overall_status)}
            </div>
            <div className="verifier-summary-text">
              <strong>Status general: {statusLabel(result.summary.overall_status)}</strong>
              <span>
                {result.summary.total_checks} verificari:{" "}
                {result.summary.pass_count} conforme, {result.summary.warning_count} atentionari,{" "}
                {result.summary.fail_count} neconforme
              </span>
            </div>
          </div>

          {/* Checks list */}
          <div className="verifier-checks">
            <h3>Verificari individuale</h3>
            {result.checks.map((check) => (
              <div key={check.id} className={`verifier-check verifier-check-${check.status}`}>
                <div className="verifier-check-header">
                  <span className="verifier-check-icon">{statusIcon(check.status)}</span>
                  <span className="verifier-check-label">{check.label}</span>
                  <span className={`verifier-badge verifier-badge-${check.status}`}>
                    {statusLabel(check.status)}
                  </span>
                </div>
                <p className="verifier-check-details">{check.details}</p>
              </div>
            ))}
          </div>

          {/* Full report */}
          {result.report_markdown && (
            <div className="verifier-report">
              <h3>Raport detaliat</h3>
              <div className="bep-rendered">
                <Markdown remarkPlugins={[remarkGfm]}>{result.report_markdown}</Markdown>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
