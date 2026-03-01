import { useState, useEffect } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import ProjectContextForm from "./ProjectContextForm";
import { createDefaultProjectContext, type ProjectContext } from "../types/projectContext";
import { useProject } from "../contexts/ProjectProvider";
import type { BepContext } from "../App";

interface Props {
  onBepGenerated?: (ctx: BepContext) => void;
  onGoToChat?: () => void;
}

export default function ProjectContextFormDemo({ onBepGenerated, onGoToChat }: Props) {
  const { currentProject } = useProject();
  const [ctx, setCtx] = useState<ProjectContext>(createDefaultProjectContext);
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showJson, setShowJson] = useState(false);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);

  // Pre-fill form from project data when project changes
  useEffect(() => {
    if (currentProject) {
      setCtx((prev) => ({
        ...prev,
        project_name: currentProject.name,
        project_code: currentProject.code,
        client_name: currentProject.client_name || prev.client_name,
        project_type: (currentProject.project_type as ProjectContext["project_type"]) || prev.project_type,
      }));
      // Try loading existing ProjectContext from backend
      fetch(`/api/projects/${currentProject.id}`)
        .then((r) => r.ok ? r.json() : null)
        .then((data) => {
          if (data?.project_context?.context_json) {
            // Restore full context from backend
            const saved = data.project_context.context_json;
            setCtx((prev) => ({
              ...prev,
              ...fromBackendContext(saved),
            }));
          }
          if (data?.latest_bep?.content_markdown) {
            setResult(data.latest_bep.content_markdown);
          } else {
            setResult(null);
          }
        })
        .catch(() => {/* ignore */});
      setSavedMsg(null);
    }
  }, [currentProject?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  /** Convert backend ProjectContext dict back to frontend shape */
  function fromBackendContext(saved: Record<string, unknown>): Partial<ProjectContext> {
    return {
      project_name: (saved.project_name as string) || "",
      project_code: (saved.project_code as string) || "",
      project_type: (saved.project_type as ProjectContext["project_type"]) || "building",
      project_description: (saved.project_description as string) || "",
      location_city: (saved.location_city as string) || "",
      location_county: (saved.location_county as string) || "",
      location_country: (saved.location_country as string) || "Romania",
      client_name: (saved.client_name as string) || "",
      client_type: (saved.client_type as ProjectContext["client_type"]) || "public",
      designer_name: (saved.designer_name as string) || "",
      current_phase: (saved.current_phase as ProjectContext["current_phase"]) || "PT",
      bep_version: (saved.bep_version as string) || "1.0",
      disciplines: (saved.disciplines as ProjectContext["disciplines"]) || [],
      cde_platform: (saved.cde_platform as ProjectContext["cde_platform"]) || "acc",
      main_exchange_format: (saved.main_exchange_format as ProjectContext["main_exchange_format"]) || "ifc4_3",
    };
  }

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
    if (!currentProject) {
      setError("Selecteaza sau creeaza un proiect mai intai.");
      return;
    }
    if (!ctx.project_name || !ctx.project_code || !ctx.client_name) {
      setError("Completeaza campurile obligatorii: Nume proiect, Cod proiect, Client.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setSavedMsg(null);

    const payload = toBackendPayload(ctx);

    try {
      // Use project-scoped endpoint
      const res = await fetch(`/api/projects/${currentProject.id}/generate-bep`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(err.detail || `Eroare server: ${res.status}`);
      }

      const data = await res.json();
      const bepMd = data.bep_document.content_markdown;
      setResult(bepMd);
      setSavedMsg(`BEP salvat pentru proiectul "${currentProject.name}" (doc #${data.bep_document.id})`);
      onBepGenerated?.({
        projectCode: currentProject.code,
        projectName: currentProject.name,
        bepMarkdown: bepMd,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Eroare necunoscuta");
    } finally {
      setLoading(false);
    }
  }

  async function handleDownloadDocx() {
    if (!currentProject) return;
    try {
      const res = await fetch(`/api/projects/${currentProject.id}/export-bep-docx`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        setError(err.detail || `Eroare la descarcarea DOCX: ${res.status}`);
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `BEP_${currentProject.code}.docx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Eroare la descarcarea DOCX");
    }
  }

  return (
    <div className="demo-container">
      <header className="demo-header">
        <div className="demo-brand">
          <div className="demo-logo">BIM</div>
          <div>
            <h1>Fisa de proiect BEP 2.0</h1>
            <p>
              {currentProject
                ? `Proiect: ${currentProject.name} (${currentProject.code})`
                : "Selecteaza sau creeaza un proiect din bara de navigare"}
            </p>
          </div>
        </div>
      </header>

      {!currentProject && (
        <div className="verifier-no-bep">
          Nu exista proiect selectat. Creeaza un proiect nou din butonul <strong>+ Proiect nou</strong> din bara de sus.
        </div>
      )}

      <ProjectContextForm value={ctx} onChange={setCtx} />

      <div className="demo-actions">
        <button className="btn-primary" onClick={handleSubmit} disabled={loading || !currentProject}>
          {loading ? "Se genereaza BEP..." : "Genereaza BEP"}
        </button>
        <button className="btn-outline" onClick={() => setShowJson(!showJson)}>
          {showJson ? "Ascunde JSON" : "Arata JSON debug"}
        </button>
        <button className="btn-outline" onClick={() => setCtx(createDefaultProjectContext())}>
          Reset la default
        </button>
      </div>

      {error && <div className="demo-alert error">{error}</div>}
      {savedMsg && <div className="demo-alert success">{savedMsg}</div>}

      {result && (
        <div className="demo-result">
          <div className="demo-result-header">
            <h3>BEP generat</h3>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button className="btn-download" onClick={handleDownloadDocx}>
                Descarca DOCX
              </button>
              {onGoToChat && (
                <button className="btn-chat-link" onClick={onGoToChat}>
                  Intreaba Expert BIM despre acest BEP &rarr;
                </button>
              )}
            </div>
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
