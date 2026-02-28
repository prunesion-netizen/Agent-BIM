import { type ChangeEvent } from "react";
import type {
  ProjectContext,
  ProjectType,
  ProjectPhase,
  CdePlatform,
  CdeModule,
  Discipline,
  ExchangeFormat,
  ClashTool,
  ClientType,
} from "../types/projectContext";

interface Props {
  value: ProjectContext;
  onChange: (value: ProjectContext) => void;
}

/* ── Option maps ──────────────────────────────────────────────────────── */

const PROJECT_TYPES: Record<ProjectType, string> = {
  building: "Cladire",
  hospital: "Spital / Sanatate",
  landfill: "Infrastructura de mediu",
  infrastructure: "Infrastructura",
  industrial: "Industrial",
  other: "Altele",
};

const PHASES: Record<ProjectPhase, string> = {
  precontract: "Pre-contract",
  PT: "PT — Proiect Tehnic",
  DDE: "DDE — Detalii de Executie",
  execution: "Executie",
  asbuilt: "As-Built / Receptie",
};

const CDE_PLATFORMS: Record<CdePlatform, string> = {
  acc: "Autodesk Construction Cloud (ACC)",
  trimble: "Trimble Connect",
  bimcollab: "BIMcollab",
  sharepoint: "SharePoint / OneDrive",
  other: "Alta platforma",
};

const CDE_MODULES_OPTIONS: Record<CdeModule, string> = {
  docs: "Docs",
  coordinate: "Coordinate",
  build: "Build",
  takeoff: "Takeoff",
  issues: "Issues",
  other: "Altele",
};

const DISCIPLINES_OPTIONS: Record<Discipline, string> = {
  architecture: "Arhitectura",
  structure: "Structuri",
  mep: "MEP (Instalatii)",
  civil: "Inginerie civila",
  roads: "Drumuri",
  infrastructure: "Infrastructura",
  other: "Altele",
};

const EXCHANGE_FORMATS: Record<ExchangeFormat, string> = {
  ifc4_3: "IFC 4.3",
  ifc2x3: "IFC 2x3",
  nwd: "NWD (Navisworks)",
  nwc: "NWC",
  dwg: "DWG",
  other: "Altul",
};

const CLASH_TOOLS: Record<ClashTool, string> = {
  navisworks: "Autodesk Navisworks",
  acc_coordinate: "ACC Coordinate",
  bimcollab: "BIMcollab",
  other: "Altul",
};

const CLIENT_TYPES: Record<ClientType, string> = {
  public: "Public",
  private: "Privat",
};

/* ── Component ────────────────────────────────────────────────────────── */

export default function ProjectContextForm({ value, onChange }: Props) {
  /* helpers */
  const set = <K extends keyof ProjectContext>(key: K, val: ProjectContext[K]) =>
    onChange({ ...value, [key]: val });

  const onText = (key: keyof ProjectContext) => (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    set(key, e.target.value as never);

  const onSelect = <K extends keyof ProjectContext>(key: K) => (e: ChangeEvent<HTMLSelectElement>) =>
    set(key, e.target.value as ProjectContext[K]);

  const onCheck = (key: keyof ProjectContext) => (e: ChangeEvent<HTMLInputElement>) =>
    set(key, e.target.checked as never);

  const onLines = (key: "client_bim_goals" | "internal_bim_goals") => (e: ChangeEvent<HTMLTextAreaElement>) =>
    set(key, e.target.value.split("\n"));

  /* multi-check toggles */
  const toggleModule = (mod: CdeModule) => {
    const next = value.cde_modules.includes(mod)
      ? value.cde_modules.filter((m) => m !== mod)
      : [...value.cde_modules, mod];
    set("cde_modules", next);
  };

  const toggleDiscipline = (d: Discipline) => {
    const next = value.disciplines.includes(d)
      ? value.disciplines.filter((x) => x !== d)
      : [...value.disciplines, d];
    set("disciplines", next);
  };

  return (
    <div className="pcf">
      {/* ════════ SECTIUNEA 1 ════════ */}
      <fieldset className="pcf-section">
        <legend>1. Identificare proiect</legend>
        <div className="pcf-grid">
          <label className="pcf-field">
            <span>Nume proiect *</span>
            <input value={value.project_name} onChange={onText("project_name")} placeholder="Ex: Construire Celula 3 Ghizela" />
          </label>
          <label className="pcf-field">
            <span>Cod proiect *</span>
            <input value={value.project_code} onChange={onText("project_code")} placeholder="Ex: GHZ-C3" />
          </label>
          <label className="pcf-field">
            <span>Tip proiect *</span>
            <select value={value.project_type} onChange={onSelect("project_type")}>
              {Object.entries(PROJECT_TYPES).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </label>
          <label className="pcf-field">
            <span>Faza curenta *</span>
            <select value={value.current_phase} onChange={onSelect("current_phase")}>
              {Object.entries(PHASES).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </label>
          <label className="pcf-field full">
            <span>Descriere proiect</span>
            <textarea value={value.project_description ?? ""} onChange={onText("project_description")} rows={2} placeholder="Descriere scurta a proiectului..." />
          </label>
        </div>
      </fieldset>

      {/* ════════ SECTIUNEA 2 ════════ */}
      <fieldset className="pcf-section">
        <legend>2. Locatie si parti implicate</legend>
        <div className="pcf-grid">
          <label className="pcf-field">
            <span>Oras</span>
            <input value={value.location_city ?? ""} onChange={onText("location_city")} />
          </label>
          <label className="pcf-field">
            <span>Judet</span>
            <input value={value.location_county ?? ""} onChange={onText("location_county")} />
          </label>
          <label className="pcf-field">
            <span>Tara</span>
            <input value={value.location_country ?? ""} onChange={onText("location_country")} />
          </label>
          <label className="pcf-field">
            <span>Client / Beneficiar *</span>
            <input value={value.client_name} onChange={onText("client_name")} placeholder="Ex: Consiliul Judetean Timis" />
          </label>
          <label className="pcf-field">
            <span>Tip client</span>
            <select value={value.client_type} onChange={onSelect("client_type")}>
              {Object.entries(CLIENT_TYPES).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </label>
          <label className="pcf-field">
            <span>Proiectant general</span>
            <input value={value.designer_name ?? ""} onChange={onText("designer_name")} />
          </label>
          <label className="pcf-field">
            <span>Nr. proiect intern</span>
            <input value={value.internal_project_number ?? ""} onChange={onText("internal_project_number")} />
          </label>
          <label className="pcf-field">
            <span>Nr. contract proiectare</span>
            <input value={value.design_contract_number ?? ""} onChange={onText("design_contract_number")} />
          </label>
          <label className="pcf-field">
            <span>Nr. contract executie</span>
            <input value={value.construction_contract_number ?? ""} onChange={onText("construction_contract_number")} />
          </label>
        </div>
      </fieldset>

      {/* ════════ SECTIUNEA 3 ════════ */}
      <fieldset className="pcf-section">
        <legend>3. Versiune BEP si EIR</legend>
        <div className="pcf-grid">
          <label className="pcf-field">
            <span>Data BEP</span>
            <input type="date" value={value.bep_date} onChange={onText("bep_date")} />
          </label>
          <label className="pcf-field">
            <span>Versiune BEP</span>
            <input value={value.bep_version} onChange={onText("bep_version")} />
          </label>
          <label className="pcf-field pcf-checkbox">
            <input type="checkbox" checked={value.has_eir} onChange={onCheck("has_eir")} />
            <span>Exista EIR (Employer's Information Requirements)</span>
          </label>
          {value.has_eir && (
            <label className="pcf-field">
              <span>ID document EIR</span>
              <input value={value.eir_document_id ?? ""} onChange={onText("eir_document_id")} />
            </label>
          )}
          <label className="pcf-field full">
            <span>Obiective BIM ale clientului (un obiectiv pe linie)</span>
            <textarea
              value={value.client_bim_goals.join("\n")}
              onChange={onLines("client_bim_goals")}
              rows={3}
              placeholder={"Vizualizare 3D\nControl cantitativ\nDocumentatie As-Built digitala"}
            />
          </label>
          <label className="pcf-field full">
            <span>Obiective BIM interne (un obiectiv pe linie)</span>
            <textarea
              value={value.internal_bim_goals.join("\n")}
              onChange={onLines("internal_bim_goals")}
              rows={3}
              placeholder={"Coordonare multi-disciplinara\nReducere erori de proiectare"}
            />
          </label>
        </div>
      </fieldset>

      {/* ════════ SECTIUNEA 4 ════════ */}
      <fieldset className="pcf-section">
        <legend>4. Echipa BIM (JSON)</legend>
        <label className="pcf-field full">
          <span>Roluri echipa BIM (format JSON)</span>
          <textarea
            className="pcf-mono"
            value={value.bim_team_roles_json}
            onChange={onText("bim_team_roles_json")}
            rows={8}
          />
        </label>
      </fieldset>

      {/* ════════ SECTIUNEA 5 ════════ */}
      <fieldset className="pcf-section">
        <legend>5. CDE (Common Data Environment)</legend>
        <div className="pcf-grid">
          <label className="pcf-field">
            <span>Platforma CDE *</span>
            <select value={value.cde_platform} onChange={onSelect("cde_platform")}>
              {Object.entries(CDE_PLATFORMS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </label>
          <div className="pcf-field">
            <span>Module CDE</span>
            <div className="pcf-check-row">
              {Object.entries(CDE_MODULES_OPTIONS).map(([k, v]) => (
                <label key={k} className="pcf-pill">
                  <input
                    type="checkbox"
                    checked={value.cde_modules.includes(k as CdeModule)}
                    onChange={() => toggleModule(k as CdeModule)}
                  />
                  {v}
                </label>
              ))}
            </div>
          </div>
          <label className="pcf-field pcf-checkbox">
            <input type="checkbox" checked={value.has_custom_cde_structure} onChange={onCheck("has_custom_cde_structure")} />
            <span>Structura CDE personalizata</span>
          </label>
          <label className="pcf-field full">
            <span>Conventie denumire documente</span>
            <input value={value.document_naming_convention ?? ""} onChange={onText("document_naming_convention")} placeholder="[PROIECT]-[DISCIPLINA]-[TIP]-[NR]-[REV]" />
          </label>
        </div>
      </fieldset>

      {/* ════════ SECTIUNEA 6 ════════ */}
      <fieldset className="pcf-section">
        <legend>6. Standarde BIM</legend>
        <div className="pcf-grid">
          <div className="pcf-field">
            <span>Standarde ISO 19650</span>
            <div className="pcf-check-col">
              <label className="pcf-checkbox">
                <input type="checkbox" checked={value.iso_19650_1} onChange={onCheck("iso_19650_1")} />
                <span>ISO 19650-1 (Concepte si principii)</span>
              </label>
              <label className="pcf-checkbox">
                <input type="checkbox" checked={value.iso_19650_2} onChange={onCheck("iso_19650_2")} />
                <span>ISO 19650-2 (Faza de livrare)</span>
              </label>
              <label className="pcf-checkbox">
                <input type="checkbox" checked={value.iso_19650_3} onChange={onCheck("iso_19650_3")} />
                <span>ISO 19650-3 (Faza operationala)</span>
              </label>
            </div>
          </div>
          <label className="pcf-field">
            <span>Alte standarde BIM</span>
            <input value={value.other_bim_standards} onChange={onText("other_bim_standards")} placeholder="BS EN 17412-1:2021, ..." />
          </label>
          <label className="pcf-field">
            <span>Standarde nationale</span>
            <input value={value.national_standards} onChange={onText("national_standards")} placeholder="RTC 8, RTC 9, ..." />
          </label>
        </div>
      </fieldset>

      {/* ════════ SECTIUNEA 7 ════════ */}
      <fieldset className="pcf-section">
        <legend>7. Software</legend>
        <div className="pcf-grid">
          <label className="pcf-field full">
            <span>Software proiectare (JSON)</span>
            <textarea className="pcf-mono" value={value.design_software_json} onChange={onText("design_software_json")} rows={5} />
          </label>
          <label className="pcf-field full">
            <span>Software coordonare (JSON)</span>
            <textarea className="pcf-mono" value={value.coordination_software_json} onChange={onText("coordination_software_json")} rows={4} />
          </label>
        </div>
      </fieldset>

      {/* ════════ SECTIUNEA 8 ════════ */}
      <fieldset className="pcf-section">
        <legend>8. Discipline si modele</legend>
        <div className="pcf-grid">
          <div className="pcf-field full">
            <span>Discipline BIM *</span>
            <div className="pcf-check-row">
              {Object.entries(DISCIPLINES_OPTIONS).map(([k, v]) => (
                <label key={k} className="pcf-pill">
                  <input
                    type="checkbox"
                    checked={value.disciplines.includes(k as Discipline)}
                    onChange={() => toggleDiscipline(k as Discipline)}
                  />
                  {v}
                </label>
              ))}
            </div>
          </div>
          <label className="pcf-field pcf-checkbox">
            <input type="checkbox" checked={value.uses_federated_models} onChange={onCheck("uses_federated_models")} />
            <span>Foloseste modele federate</span>
          </label>
          <label className="pcf-field">
            <span>Format principal de schimb</span>
            <select value={value.main_exchange_format} onChange={onSelect("main_exchange_format")}>
              {Object.entries(EXCHANGE_FORMATS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </label>
        </div>
      </fieldset>

      {/* ════════ SECTIUNEA 9 ════════ */}
      <fieldset className="pcf-section">
        <legend>9. Nivele de detaliu LOD / LOI</legend>
        <div className="pcf-grid">
          <label className="pcf-field">
            <span>Scala LOD</span>
            <input value={value.lod_scale ?? ""} onChange={onText("lod_scale")} placeholder="LOD 100-400 (BIMForum/RIBA)" />
          </label>
          <label className="pcf-field">
            <span>LOD tinta PT</span>
            <input value={value.lod_target_pt ?? ""} onChange={onText("lod_target_pt")} placeholder="200-300" />
          </label>
          <label className="pcf-field">
            <span>LOD tinta DDE</span>
            <input value={value.lod_target_dde ?? ""} onChange={onText("lod_target_dde")} placeholder="300-350" />
          </label>
          <label className="pcf-field">
            <span>LOD tinta Executie</span>
            <input value={value.lod_target_execution ?? ""} onChange={onText("lod_target_execution")} placeholder="350-400" />
          </label>
          <label className="pcf-field full">
            <span>Cerinte speciale LOI</span>
            <textarea value={value.loi_special_requirements} onChange={onText("loi_special_requirements")} rows={2} placeholder="Cerinte suplimentare de informatii..." />
          </label>
        </div>
      </fieldset>

      {/* ════════ SECTIUNEA 10 ════════ */}
      <fieldset className="pcf-section">
        <legend>10. Livrabile si jaloane</legend>
        <div className="pcf-grid">
          <label className="pcf-field full">
            <span>Jaloane BIM (un jalon pe linie)</span>
            <textarea value={value.bim_milestones} onChange={onText("bim_milestones")} rows={4} />
          </label>
          <label className="pcf-field full">
            <span>Tipuri livrabile BIM (un tip pe linie)</span>
            <textarea value={value.bim_deliverable_types} onChange={onText("bim_deliverable_types")} rows={4} />
          </label>
        </div>
      </fieldset>

      {/* ════════ SECTIUNEA 11 ════════ */}
      <fieldset className="pcf-section">
        <legend>11. Coordonare si calitate</legend>
        <div className="pcf-grid">
          <label className="pcf-field">
            <span>Frecventa sedinte proiectare</span>
            <input value={value.coordination_meeting_design_frequency ?? ""} onChange={onText("coordination_meeting_design_frequency")} placeholder="Saptamanal" />
          </label>
          <label className="pcf-field">
            <span>Frecventa sedinte executie</span>
            <input value={value.coordination_meeting_execution_frequency ?? ""} onChange={onText("coordination_meeting_execution_frequency")} placeholder="Bi-saptamanal" />
          </label>
          <label className="pcf-field">
            <span>Instrument clash detection</span>
            <select value={value.clash_detection_tool} onChange={onSelect("clash_detection_tool")}>
              {Object.entries(CLASH_TOOLS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </label>
          <label className="pcf-field">
            <span>Toleranta clash critic DDE</span>
            <input value={value.clash_tolerance_critical_dde ?? ""} onChange={onText("clash_tolerance_critical_dde")} />
          </label>
          <label className="pcf-field full">
            <span>KPI-uri BIM (un KPI pe linie)</span>
            <textarea value={value.bim_kpis} onChange={onText("bim_kpis")} rows={3} />
          </label>
        </div>
      </fieldset>
    </div>
  );
}
