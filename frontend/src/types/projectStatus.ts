/** Mapping status -> label romanesc, culoare, iconita */

export interface StatusInfo {
  label: string;
  short: string;
  color: string;
  icon: string;
}

export const PROJECT_STATUS_MAP: Record<string, StatusInfo> = {
  new: {
    label: "Proiect nou",
    short: "Nou",
    color: "gray",
    icon: "\u25CB",          // ○
  },
  context_defined: {
    label: "Context definit",
    short: "Context",
    color: "blue",
    icon: "\u25D4",          // ◔
  },
  bep_generated: {
    label: "BEP generat",
    short: "BEP",
    color: "amber",
    icon: "\u25D1",          // ◑
  },
  bep_verified_partial: {
    label: "Verificat partial",
    short: "Partial",
    color: "orange",
    icon: "\u26A0",          // ⚠
  },
  bep_verified_ok: {
    label: "Verificat OK",
    short: "OK",
    color: "green",
    icon: "\u2713",          // ✓
  },
};

export function getStatusInfo(status: string): StatusInfo {
  return PROJECT_STATUS_MAP[status] ?? PROJECT_STATUS_MAP.new;
}
