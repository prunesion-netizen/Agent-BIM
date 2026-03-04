/**
 * CdeStateBadge — Badge colorat pentru starea CDE a unui document.
 * WIP=gri, Shared=albastru, Published=verde, Archived=amber
 */

interface Props {
  state: string | null | undefined;
}

const STATE_CONFIG: Record<string, { label: string; className: string }> = {
  wip: { label: "WIP", className: "cde-badge cde-wip" },
  shared: { label: "Shared", className: "cde-badge cde-shared" },
  published: { label: "Published", className: "cde-badge cde-published" },
  archived: { label: "Archived", className: "cde-badge cde-archived" },
};

export default function CdeStateBadge({ state }: Props) {
  const config = STATE_CONFIG[state || "wip"] || STATE_CONFIG.wip;
  return <span className={config.className}>{config.label}</span>;
}
