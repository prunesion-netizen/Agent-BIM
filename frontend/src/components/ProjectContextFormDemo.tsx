import { useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import ProjectContextForm from "./ProjectContextForm";
import { createDefaultProjectContext, type ProjectContext } from "../types/projectContext";
import type { BepContext } from "../App";

interface Props {
  onBepGenerated?: (ctx: BepContext) => void;
  onGoToChat?: () => void;
}

export default function ProjectContextFormDemo({ onBepGenerated, onGoToChat }: Props) {
  const [ctx, setCtx] = useState<ProjectContext>(createDefaultProjectContext);
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showJson, setShowJson] = useState(false);

  /** Transform front-end shape → backend Pydantic shape */
  function toBackendPayload(c: ProjectContext) {
    let bim_team_roles = [];
    try { bim_team_roles = JSON.parse(c.bim_team_roles_json); } catch { /* keep empty */ }

    let design_software = [];
    try { design_software = JSON.parse(c.design_software_json); } catch { /* keep empty */ }

    let coordination_software = [];
    try { coordination_software = JSON.parse(c.coordination_software_json); } catch { /* keep empty */ }

    return {
      project_name: c.project_name,
      project_code: c.project_code,
      project_type: c.project_type,
      project_description: c.project_description || null,
      location_city: c.location_city || null,
      location_county: c.location_county || null,
      location_country: c.location_country || null,
      client_name: c.client_name,
      client_type: c.client_type,
      designer_name: c.designer_name || null,
      internal_project_number: c.internal_project_number || null,
      design_contract_number: c.design_contract_number || null,
      construction_contract_number: c.construction_contract_number || null,
      current_phase: c.current_phase,
      bep_date: c.bep_date,
      bep_version: c.bep_version,
      has_eir: c.has_eir,
      eir_document_id: c.eir_document_id || null,
      client_bim_goals: c.client_bim_goals.filter(Boolean),
      internal_bim_goals: c.internal_bim_goals.filter(Boolean),
      bim_team_roles,
      cde_platform: c.cde_platform,
      cde_modules: c.cde_modules,
      has_custom_cde_structure: c.has_custom_cde_structure,
      document_naming_convention: c.document_naming_convention || null,
      iso_19650_1: c.iso_19650_1,
      iso_19650_2: c.iso_19650_2,
      iso_19650_3: c.iso_19650_3,
      other_bim_standards: c.other_bim_standards.split(",").map(s => s.trim()).filter(Boolean),
      national_standards: c.national_standards.split(",").map(s => s.trim()).filter(Boolean),
      design_software,
      coordination_software,
      planning_cost_software: [],
      disciplines: c.disciplines,
      uses_federated_models: c.uses_federated_models,
      main_exchange_format: c.main_exchange_format,
      lod_scale: c.lod_scale || null,
      lod_target_pt: c.lod_target_pt || null,
      lod_target_dde: c.lod_target_dde || null,
      lod_target_execution: c.lod_target_execution || null,
      loi_special_requirements: c.loi_special_requirements.split("\n").filter(Boolean),
      bim_milestones: c.bim_milestones.split("\n").filter(Boolean),
      bim_deliverable_types: c.bim_deliverable_types.split("\n").filter(Boolean),
      coordination_meeting_design_frequency: c.coordination_meeting_design_frequency || null,
      coordination_meeting_execution_frequency: c.coordination_meeting_execution_frequency || null,
      clash_detection_tool: c.clash_detection_tool,
      clash_tolerance_critical_dde: c.clash_tolerance_critical_dde || null,
      bim_kpis: c.bim_kpis.split("\n").filter(Boolean),
    };
  }

  async function handleSubmit() {
    if (!ctx.project_name || !ctx.project_code || !ctx.client_name) {
      setError("Completeaza campurile obligatorii: Nume proiect, Cod proiect, Client.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const payload = toBackendPayload(ctx);

    try {
      const res = await fetch("/api/generate-bep", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(err.detail || `Eroare server: ${res.status}`);
      }

      const data = await res.json();
      setResult(data.bep_markdown);
      onBepGenerated?.({
        projectCode: data.project_code,
        projectName: ctx.project_name,
        bepMarkdown: data.bep_markdown,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Eroare necunoscuta");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="demo-container">
      <header className="demo-header">
        <div className="demo-brand">
          <div className="demo-logo">BIM</div>
          <div>
            <h1>Fisa de proiect BEP 2.0</h1>
            <p>Completeaza datele proiectului pentru a genera un BEP conform ISO 19650-2</p>
          </div>
        </div>
      </header>

      <ProjectContextForm value={ctx} onChange={setCtx} />

      <div className="demo-actions">
        <button className="btn-primary" onClick={handleSubmit} disabled={loading}>
          {loading ? "Se genereaza BEP..." : "Genereaza BEP"}
        </button>
        <button className="btn-outline" onClick={() => setShowJson(!showJson)}>
          {showJson ? "Ascunde JSON" : "Arata JSON debug"}
        </button>
        <button className="btn-outline" onClick={() => setCtx(createDefaultProjectContext())}>
          Reset la default
        </button>
      </div>

      {error && (
        <div className="demo-alert error">{error}</div>
      )}

      {result && (
        <div className="demo-result">
          <div className="demo-result-header">
            <h3>BEP generat</h3>
            {onGoToChat && (
              <button className="btn-chat-link" onClick={onGoToChat}>
                Intreaba Expert BIM despre acest BEP &rarr;
              </button>
            )}
          </div>
          <div className="bep-rendered">
            <Markdown remarkPlugins={[remarkGfm]}>{result}</Markdown>
          </div>
        </div>
      )}

      {showJson && (
        <div className="demo-debug">
          <h3>JSON debug — payload catre backend</h3>
          <pre>{JSON.stringify(toBackendPayload(ctx), null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
