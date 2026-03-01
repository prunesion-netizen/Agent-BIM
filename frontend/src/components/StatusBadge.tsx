import { getStatusInfo } from "../types/projectStatus";

interface Props {
  status: string;
  showLabel?: boolean;
}

export default function StatusBadge({ status, showLabel = true }: Props) {
  const info = getStatusInfo(status);
  return (
    <span className={`status-badge status-badge-${info.color}`} title={info.label}>
      <span className="status-badge-icon">{info.icon}</span>
      {showLabel && <span className="status-badge-label">{info.short}</span>}
    </span>
  );
}
