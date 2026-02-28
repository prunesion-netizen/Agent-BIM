/** Rol în echipa BIM */
export interface BimTeamRole {
  role_name: string;
  role_code: string;
  organization: string;
  person_name?: string;
  email?: string;
}

/** Software utilizat */
export interface SoftwareItem {
  name: string;
  version_min: string;
  use_case: string;
}

/** Tipuri de proiect */
export type ProjectType =
  | "building"
  | "hospital"
  | "landfill"
  | "infrastructure"
  | "industrial"
  | "other";

/** Faze proiect */
export type ProjectPhase =
  | "precontract"
  | "PT"
  | "DDE"
  | "execution"
  | "asbuilt";

/** Platforme CDE */
export type CdePlatform =
  | "acc"
  | "trimble"
  | "bimcollab"
  | "sharepoint"
  | "other";

/** Module CDE */
export type CdeModule =
  | "docs"
  | "coordinate"
  | "build"
  | "takeoff"
  | "issues"
  | "other";

/** Discipline */
export type Discipline =
  | "architecture"
  | "structure"
  | "mep"
  | "civil"
  | "roads"
  | "infrastructure"
  | "other";

/** Format de schimb */
export type ExchangeFormat =
  | "ifc4_3"
  | "ifc2x3"
  | "nwd"
  | "nwc"
  | "dwg"
  | "other";

/** Instrument clash detection */
export type ClashTool =
  | "navisworks"
  | "acc_coordinate"
  | "bimcollab"
  | "other";

/** Tipul clientului */
export type ClientType = "public" | "private";

/**
 * ProjectContext — Fișa de proiect BEP 2.0
 * Toate datele necesare pentru generarea unui BEP conform ISO 19650-2.
 * Reflectă exact schema Pydantic din backend.
 */
export interface ProjectContext {
  // ── Identificare proiect
  project_name: string;
  project_code: string;
  project_type: ProjectType;
  project_description?: string;

  // ── Locație
  location_city?: string;
  location_county?: string;
  location_country?: string;

  // ── Părți implicate
  client_name: string;
  client_type: ClientType;
  designer_name?: string;
  internal_project_number?: string;
  design_contract_number?: string;
  construction_contract_number?: string;

  // ── Faza și versiune BEP
  current_phase: ProjectPhase;
  bep_date: string; // ISO date string YYYY-MM-DD
  bep_version: string;

  // ── EIR
  has_eir: boolean;
  eir_document_id?: string;
  client_bim_goals: string[];
  internal_bim_goals: string[];

  // ── Echipa BIM (JSON textarea in v1)
  bim_team_roles_json: string;

  // ── CDE
  cde_platform: CdePlatform;
  cde_modules: CdeModule[];
  has_custom_cde_structure: boolean;
  document_naming_convention?: string;

  // ── Standarde
  iso_19650_1: boolean;
  iso_19650_2: boolean;
  iso_19650_3: boolean;
  other_bim_standards: string; // separate cu virgulă
  national_standards: string;

  // ── Software (JSON textarea in v1)
  design_software_json: string;
  coordination_software_json: string;

  // ── Discipline și modele
  disciplines: Discipline[];
  uses_federated_models: boolean;
  main_exchange_format: ExchangeFormat;

  // ── LOD
  lod_scale?: string;
  lod_target_pt?: string;
  lod_target_dde?: string;
  lod_target_execution?: string;
  loi_special_requirements: string;

  // ── Livrabile
  bim_milestones: string;
  bim_deliverable_types: string;

  // ── Coordonare
  coordination_meeting_design_frequency?: string;
  coordination_meeting_execution_frequency?: string;
  clash_detection_tool: ClashTool;
  clash_tolerance_critical_dde?: string;
  bim_kpis: string;
}

/** Valori default pentru un ProjectContext nou */
export function createDefaultProjectContext(): ProjectContext {
  const today = new Date().toISOString().slice(0, 10);
  return {
    project_name: "",
    project_code: "",
    project_type: "building",
    project_description: "",
    location_city: "",
    location_county: "",
    location_country: "Romania",
    client_name: "",
    client_type: "public",
    designer_name: "",
    internal_project_number: "",
    design_contract_number: "",
    construction_contract_number: "",
    current_phase: "PT",
    bep_date: today,
    bep_version: "1.0",
    has_eir: false,
    eir_document_id: "",
    client_bim_goals: [],
    internal_bim_goals: [],
    bim_team_roles_json: JSON.stringify(
      [
        { role_name: "BIM Manager", role_code: "BM", organization: "", person_name: "", email: "" },
        { role_name: "BIM Coordinator", role_code: "BC", organization: "", person_name: "", email: "" },
      ],
      null,
      2
    ),
    cde_platform: "acc",
    cde_modules: ["docs", "coordinate"],
    has_custom_cde_structure: false,
    document_naming_convention: "[PROIECT]-[DISCIPLINA]-[TIP]-[NR]-[REV]",
    iso_19650_1: true,
    iso_19650_2: true,
    iso_19650_3: false,
    other_bim_standards: "BS EN 17412-1:2021",
    national_standards: "RTC 8, RTC 9",
    design_software_json: JSON.stringify(
      [
        { name: "Autodesk Revit", version_min: "2024", use_case: "Modelare 3D BIM" },
        { name: "AutoCAD Civil 3D", version_min: "2024", use_case: "Modele teren" },
      ],
      null,
      2
    ),
    coordination_software_json: JSON.stringify(
      [
        { name: "Navisworks Manage", version_min: "2024", use_case: "Clash detection, 4D" },
      ],
      null,
      2
    ),
    disciplines: ["architecture", "structure"],
    uses_federated_models: true,
    main_exchange_format: "ifc4_3",
    lod_scale: "LOD 100-400 (BIMForum/RIBA)",
    lod_target_pt: "200-300",
    lod_target_dde: "300-350",
    lod_target_execution: "350-400",
    loi_special_requirements: "",
    bim_milestones: "M0 Kick-off\nM1 Finalizare PT\nM2 Finalizare DDE\nM3 Start executie\nM7 Receptie preliminara\nM8 Receptie finala",
    bim_deliverable_types: "Model BIM federat (RVT+IFC)\nPlanuri 2D (DWG+PDF)\nRaport clash detection (BCF+PDF)\nExtrase cantitati (XLSX)",
    coordination_meeting_design_frequency: "Saptamanal",
    coordination_meeting_execution_frequency: "Bi-saptamanal",
    clash_detection_tool: "navisworks",
    clash_tolerance_critical_dde: "0 clash-uri hard la emiterea DDE",
    bim_kpis: "Nr. clash-uri hard nerezolvate: 0\n% modele la termen: >= 90%\nTimp remediere clash critic: <= 3 zile",
  };
}
