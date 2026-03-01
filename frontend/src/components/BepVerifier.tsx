import { useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { BepContext } from "../App";

interface Props {
  bepContext?: BepContext | null;
  projectId?: number | null;
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

interface CategoryRow {
  name: string;
  element_count: string;
}

/* ── Options matching backend Literal types ── */
const SOURCE_OPTIONS: { value: string; label: string }[] = [
  { value: "revit", label: "Revit" },
  { value: "ifc", label: "IFC" },
  { value: "other", label: "Altul" },
];

const DISCIPLINE_OPTIONS: { value: string; label: string }[] = [
  { value: "architecture", label: "Arhitectura" },
  { value: "structure", label: "Structura" },
  { value: "mep", label: "MEP (HVAC/Electrice/Sanitare)" },
  { value: "civil", label: "Civil" },
  { value: "roads", label: "Drumuri" },
  { value: "infrastructure", label: "Infrastructura" },
  { value: "other", label: "Altele" },
];

const FORMAT_OPTIONS: { value: string; label: string }[] = [
  { value: "ifc4_3", label: "IFC 4.3" },
  { value: "ifc2x3", label: "IFC 2x3" },
  { value: "nwd", label: "NWD" },
  { value: "nwc", label: "NWC" },
  { value: "dwg", label: "DWG" },
  { value: "other", label: "Altul" },
];

export default function BepVerifier({ bepContext, projectId }: Props) {
  const [source, setSource] = useState("revit");
  const [disciplines, setDisciplines] = useState<string[]>([]);
  const [formats, setFormats] = useState<string[]>([]);
  const [hasGeoref, setHasGeoref] = useState(false);
  const [coordSystem, setCoordSystem] = useState("");
  const [lodAvailable, setLodAvailable] = useState(false);
  const [notes, setNotes] = useState("");
  const [categories, setCategories] = useState<CategoryRow[]>([]);

  const [result, setResult] = useState<VerificationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggleItem(list: string[], item: string, setter: (v: string[]) => void) {
    setter(list.includes(item) ? list.filter((x) => x !== item) : [...list, item]);
  }

  function addCategory() {
    setCategories([...categories, { name: "", element_count: "" }]);
  }

  function updateCategory(idx: number, field: keyof CategoryRow, value: string) {
    const updated = [...categories];
    updated[idx] = { ...updated[idx], [field]: value };
    setCategories(updated);
  }

  function removeCategory(idx: number) {
    setCategories(categories.filter((_, i) => i !== idx));
  }

  async function handleVerify() {
    if (!projectId) {
      setError("Selecteaza un proiect mai intai.");
      return;
    }
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

    const modelSummary = {
      source,
      disciplines_present: disciplines,
      categories: categories
        .filter((c) => c.name.trim())
        .map((c) => ({
          name: c.name.trim(),
          element_count: parseInt(c.element_count, 10) || 0,
        })),
      has_georeference: hasGeoref,
      coordinate_system: coordSystem || null,
      exchange_formats_available: formats,
      lod_info_available: lodAvailable,
      notes: notes || null,
    };

    try {
      const res = await fetch(`/api/projects/${projectId}/verify-bep-model`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(modelSummary),
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
    if (status === "warning") return "Atentie";
    return "Neconform";
  }

  return (
    <div className="verifier-container">
      {/* Header */}
      <header className="verifier-header">
        <div className="demo-brand">
          <div
            className="demo-logo"
            style={{ background: "linear-gradient(135deg, #7c3aed, #4f46e5)" }}
          >
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
          Nu exista BEP generat. Mergi la tab-ul <strong>Fisa BEP</strong> si genereaza un
          BEP mai intai.
        </div>
      )}

      {/* Model Summary Form */}
      <div className="verifier-form">
        <fieldset className="pcf-section">
          <legend>Rezumat Model BIM</legend>

          {/* Source */}
          <div className="pcf-grid">
            <div className="pcf-field">
              <span>Sursa modelului</span>
              <select value={source} onChange={(e) => setSource(e.target.value)}>
                {SOURCE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Disciplines */}
          <div className="pcf-field full" style={{ marginTop: 16 }}>
            <span>Discipline prezente in model</span>
            <div className="pcf-check-row">
              {DISCIPLINE_OPTIONS.map((d) => (
                <label key={d.value} className="pcf-pill">
                  <input
                    type="checkbox"
                    checked={disciplines.includes(d.value)}
                    onChange={() => toggleItem(disciplines, d.value, setDisciplines)}
                  />
                  {d.label}
                </label>
              ))}
            </div>
          </div>

          {/* Exchange formats */}
          <div className="pcf-field full" style={{ marginTop: 16 }}>
            <span>Formate de schimb disponibile</span>
            <div className="pcf-check-row">
              {FORMAT_OPTIONS.map((f) => (
                <label key={f.value} className="pcf-pill">
                  <input
                    type="checkbox"
                    checked={formats.includes(f.value)}
                    onChange={() => toggleItem(formats, f.value, setFormats)}
                  />
                  {f.label}
                </label>
              ))}
            </div>
          </div>

          {/* Georef + Coord + LOD */}
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

            <label className="pcf-field pcf-checkbox">
              <input
                type="checkbox"
                checked={lodAvailable}
                onChange={() => setLodAvailable(!lodAvailable)}
              />
              <span>Informatii LOD/LOI disponibile</span>
            </label>
          </div>

          {/* Categories */}
          <div className="pcf-field full" style={{ marginTop: 16 }}>
            <span>Categorii de elemente (optional)</span>
            {categories.map((cat, idx) => (
              <div key={idx} className="verifier-cat-row">
                <input
                  type="text"
                  value={cat.name}
                  onChange={(e) => updateCategory(idx, "name", e.target.value)}
                  placeholder="Categorie (ex: Walls)"
                  className="verifier-cat-name"
                />
                <input
                  type="number"
                  value={cat.element_count}
                  onChange={(e) => updateCategory(idx, "element_count", e.target.value)}
                  placeholder="Nr. elemente"
                  className="verifier-cat-count"
                  min={0}
                />
                <button
                  type="button"
                  className="verifier-cat-remove"
                  onClick={() => removeCategory(idx)}
                  title="Sterge"
                >
                  &times;
                </button>
              </div>
            ))}
            <button type="button" className="btn-outline verifier-cat-add" onClick={addCategory}>
              + Adauga categorie
            </button>
          </div>

          {/* Notes */}
          <div className="pcf-field full" style={{ marginTop: 16 }}>
            <span>Observatii suplimentare</span>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
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
          disabled={loading || !bepContext || !projectId}
          style={
            bepContext
              ? { background: "linear-gradient(135deg, #7c3aed, #4f46e5)" }
              : undefined
          }
        >
          {loading ? "Se verifica..." : "Ruleaza verificarea"}
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
                {result.summary.total_checks} verificari: {result.summary.pass_count} conforme,{" "}
                {result.summary.warning_count} atentionari, {result.summary.fail_count} neconforme
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
