import { useState, type FormEvent } from "react";
import { useProject } from "../contexts/ProjectProvider";
import StatusBadge from "./StatusBadge";
import { getStatusInfo } from "../types/projectStatus";

const PROJECT_TYPES = [
  { value: "building", label: "Cladire" },
  { value: "hospital", label: "Spital" },
  { value: "landfill", label: "Depozit deseuri" },
  { value: "infrastructure", label: "Infrastructura" },
  { value: "industrial", label: "Industrial" },
  { value: "other", label: "Altul" },
];

export default function ProjectSelector() {
  const { projects, currentProject, selectProject, createProject, loading } = useProject();
  const [showModal, setShowModal] = useState(false);
  const [newName, setNewName] = useState("");
  const [newCode, setNewCode] = useState("");
  const [newClient, setNewClient] = useState("");
  const [newType, setNewType] = useState("building");
  const [newDescription, setNewDescription] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!newName.trim() || !newCode.trim()) {
      setError("Completati numele si codul proiectului.");
      return;
    }
    setCreating(true);
    setError(null);
    try {
      await createProject({
        name: newName.trim(),
        code: newCode.trim(),
        client_name: newClient.trim() || undefined,
        project_type: newType,
        description: newDescription.trim() || undefined,
      });
      setShowModal(false);
      setNewName("");
      setNewCode("");
      setNewClient("");
      setNewType("building");
      setNewDescription("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Eroare necunoscuta");
    } finally {
      setCreating(false);
    }
  }

  return (
    <>
      <div className="project-selector">
        {loading ? (
          <span className="project-selector-loading">Se incarca...</span>
        ) : projects.length === 0 ? (
          <span className="project-selector-empty">Niciun proiect</span>
        ) : (
          <>
            <select
              className="project-selector-dropdown"
              value={currentProject?.id ?? ""}
              onChange={(e) => selectProject(Number(e.target.value))}
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.code}) — {getStatusInfo(p.status).short}
                </option>
              ))}
            </select>
            {currentProject && <StatusBadge status={currentProject.status} />}
          </>
        )}

        <button className="project-selector-new" onClick={() => setShowModal(true)}>
          + Proiect nou
        </button>
      </div>

      {currentProject?.description && (
        <div className="project-description-bar">
          {currentProject.description}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Proiect nou</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>
                &times;
              </button>
            </div>

            <form onSubmit={handleCreate} className="modal-form">
              <div className="pcf-field">
                <span>Nume proiect *</span>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="ex: Spital Regional Cluj"
                  autoFocus
                />
              </div>

              <div className="pcf-field">
                <span>Cod proiect *</span>
                <input
                  type="text"
                  value={newCode}
                  onChange={(e) => setNewCode(e.target.value)}
                  placeholder="ex: SRC-2026"
                />
              </div>

              <div className="pcf-field">
                <span>Client (optional)</span>
                <input
                  type="text"
                  value={newClient}
                  onChange={(e) => setNewClient(e.target.value)}
                  placeholder="ex: Ministerul Sanatatii"
                />
              </div>

              <div className="pcf-field">
                <span>Tip proiect</span>
                <select value={newType} onChange={(e) => setNewType(e.target.value)}>
                  {PROJECT_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="pcf-field">
                <span>Descriere (optional)</span>
                <textarea
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="Descriere scurta a proiectului..."
                  rows={2}
                />
              </div>

              {error && <div className="demo-alert error">{error}</div>}

              <div className="modal-actions">
                <button type="button" className="btn-outline" onClick={() => setShowModal(false)}>
                  Anuleaza
                </button>
                <button type="submit" className="btn-primary" disabled={creating}>
                  {creating ? "Se creeaza..." : "Creeaza proiect"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
