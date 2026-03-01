import { useState, useRef, useEffect, type FormEvent } from "react";
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
  const { projects, currentProject, selectProject, createProject, updateProject, loading } = useProject();
  const [showModal, setShowModal] = useState(false);
  const [newName, setNewName] = useState("");
  const [newCode, setNewCode] = useState("");
  const [newClient, setNewClient] = useState("");
  const [newType, setNewType] = useState("building");
  const [newDescription, setNewDescription] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Inline edit name
  const [editingName, setEditingName] = useState(false);
  const [editName, setEditName] = useState("");
  const [savingName, setSavingName] = useState(false);
  const nameRef = useRef<HTMLInputElement>(null);

  // Inline edit description
  const [editingDesc, setEditingDesc] = useState(false);
  const [editDesc, setEditDesc] = useState("");
  const [savingDesc, setSavingDesc] = useState(false);
  const editRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (editingName && nameRef.current) {
      nameRef.current.focus();
      nameRef.current.select();
    }
  }, [editingName]);

  useEffect(() => {
    if (editingDesc && editRef.current) {
      editRef.current.focus();
      editRef.current.select();
    }
  }, [editingDesc]);

  function startEditName() {
    setEditName(currentProject?.name ?? "");
    setEditingName(true);
  }

  async function saveName() {
    if (!currentProject || !editName.trim()) return;
    setSavingName(true);
    try {
      await updateProject(currentProject.id, { name: editName.trim() });
      setEditingName(false);
    } catch {
      // keep editing on error
    } finally {
      setSavingName(false);
    }
  }

  function cancelEditName() {
    setEditingName(false);
  }

  function startEditDesc() {
    setEditDesc(currentProject?.description ?? "");
    setEditingDesc(true);
  }

  async function saveDesc() {
    if (!currentProject) return;
    setSavingDesc(true);
    try {
      await updateProject(currentProject.id, {
        description: editDesc.trim() || undefined,
      });
      setEditingDesc(false);
    } catch {
      // keep editing on error
    } finally {
      setSavingDesc(false);
    }
  }

  function cancelEditDesc() {
    setEditingDesc(false);
  }

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
      {currentProject && (
        <div className="project-name-bar">
          {editingName ? (
            <div className="name-edit-row">
              <input
                ref={nameRef}
                className="name-edit-input"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") { e.preventDefault(); saveName(); }
                  if (e.key === "Escape") cancelEditName();
                }}
                disabled={savingName}
              />
              <button className="btn-sm btn-primary" onClick={saveName} disabled={savingName || !editName.trim()}>
                {savingName ? "..." : "Salveaza"}
              </button>
              <button className="btn-sm btn-outline" onClick={cancelEditName} disabled={savingName}>
                Anuleaza
              </button>
            </div>
          ) : (
            <div className="name-display-row">
              <span className="name-text">{currentProject.name}</span>
              <span className="name-code">({currentProject.code})</span>
              <button className="desc-edit-btn" onClick={startEditName} title="Editeaza numele">
                &#9998;
              </button>
            </div>
          )}
        </div>
      )}

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

      {currentProject && (
        <div className="project-description-bar">
          {editingDesc ? (
            <div className="desc-edit-row">
              <textarea
                ref={editRef}
                className="desc-edit-input"
                value={editDesc}
                onChange={(e) => setEditDesc(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); saveDesc(); }
                  if (e.key === "Escape") cancelEditDesc();
                }}
                rows={2}
                disabled={savingDesc}
              />
              <div className="desc-edit-actions">
                <button className="btn-sm btn-primary" onClick={saveDesc} disabled={savingDesc}>
                  {savingDesc ? "..." : "Salveaza"}
                </button>
                <button className="btn-sm btn-outline" onClick={cancelEditDesc} disabled={savingDesc}>
                  Anuleaza
                </button>
              </div>
            </div>
          ) : (
            <div className="desc-display-row">
              <span className="desc-text">
                {currentProject.description || "Fara descriere"}
              </span>
              <button className="desc-edit-btn" onClick={startEditDesc} title="Editeaza descrierea">
                &#9998;
              </button>
            </div>
          )}
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
