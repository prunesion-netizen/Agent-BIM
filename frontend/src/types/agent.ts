/**
 * agent.ts — TypeScript types pentru Agent BIM SSE events.
 */

/** SSE event: agentul apelează un tool */
export interface ToolCallEvent {
  type: "tool_call";
  tool_name: string;
  tool_input: Record<string, unknown>;
  call_id: string;
}

/** SSE event: rezultatul execuției unui tool */
export interface ToolResultEvent {
  type: "tool_result";
  call_id: string;
  tool_name: string;
  result: Record<string, unknown>;
  duration_ms: number;
}

/** SSE event: text de la agent */
export interface TextDeltaEvent {
  type: "text_delta";
  content: string;
}

/** SSE event: eroare */
export interface ErrorEvent {
  type: "error";
  message: string;
}

/** SSE event: agentul a terminat */
export interface DoneEvent {
  type: "done";
}

export type AgentSSEEvent =
  | ToolCallEvent
  | ToolResultEvent
  | TextDeltaEvent
  | ErrorEvent
  | DoneEvent;

/** Un pas de tool call cu rezultat asociat */
export interface ToolStep {
  call_id: string;
  tool_name: string;
  tool_input: Record<string, unknown>;
  result?: Record<string, unknown>;
  duration_ms?: number;
  status: "running" | "completed" | "error";
}

/** Un mesaj din conversația cu agentul */
export interface AgentMessage {
  id: number;
  role: "user" | "assistant" | "system";
  content: string;
  toolSteps?: ToolStep[];
}

/** Tool name → human-readable label */
export const TOOL_LABELS: Record<string, string> = {
  get_project_info: "Informații proiect",
  get_project_context: "Fișa BEP",
  generate_bep: "Generare BEP",
  verify_bep: "Verificare BEP",
  export_bep_docx: "Export DOCX",
  update_project_context: "Actualizare fișă",
  get_verification_history: "Istoric verificări",
  search_bim_standards: "Căutare standarde",
};
