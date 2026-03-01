import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";

/* ── Types ── */
export interface ProjectRead {
  id: number;
  name: string;
  code: string;
  client_name: string | null;
  project_type: string | null;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  code: string;
  client_name?: string;
  project_type?: string;
  description?: string;
}

export interface ProjectUpdate {
  name?: string;
  client_name?: string;
  project_type?: string;
  description?: string;
}

interface ProjectCtx {
  projects: ProjectRead[];
  currentProject: ProjectRead | null;
  loading: boolean;
  loadProjects: () => Promise<void>;
  selectProject: (id: number) => void;
  createProject: (data: ProjectCreate) => Promise<ProjectRead>;
  updateProject: (id: number, data: ProjectUpdate) => Promise<ProjectRead>;
  deleteProject: (id: number) => Promise<void>;
}

const ProjectContext = createContext<ProjectCtx | null>(null);

export function useProject(): ProjectCtx {
  const ctx = useContext(ProjectContext);
  if (!ctx) throw new Error("useProject must be used inside ProjectProvider");
  return ctx;
}

/* ── Provider ── */
export function ProjectProvider({ children }: { children: ReactNode }) {
  const [projects, setProjects] = useState<ProjectRead[]>([]);
  const [currentId, setCurrentId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const currentProject = projects.find((p) => p.id === currentId) ?? null;

  const loadProjects = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/projects");
      if (res.ok) {
        const data: ProjectRead[] = await res.json();
        setProjects(data);
        // Auto-select first project if none selected
        if (data.length > 0 && (currentId === null || !data.some((p) => p.id === currentId))) {
          setCurrentId(data[0].id);
        }
      }
    } catch {
      // silently fail on load
    } finally {
      setLoading(false);
    }
  }, [currentId]);

  const selectProject = useCallback((id: number) => {
    setCurrentId(id);
  }, []);

  const createProject = useCallback(
    async (data: ProjectCreate): Promise<ProjectRead> => {
      const res = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(err.detail || "Eroare la crearea proiectului");
      }
      const project: ProjectRead = await res.json();
      setProjects((prev) => [project, ...prev]);
      setCurrentId(project.id);
      return project;
    },
    [],
  );

  const updateProject = useCallback(
    async (id: number, data: ProjectUpdate): Promise<ProjectRead> => {
      const res = await fetch(`/api/projects/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(err.detail || "Eroare la actualizarea proiectului");
      }
      const updated: ProjectRead = await res.json();
      setProjects((prev) => prev.map((p) => (p.id === id ? updated : p)));
      return updated;
    },
    [],
  );

  const deleteProject = useCallback(
    async (id: number): Promise<void> => {
      const res = await fetch(`/api/projects/${id}`, { method: "DELETE" });
      if (!res.ok && res.status !== 204) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(err.detail || "Eroare la stergerea proiectului");
      }
      setProjects((prev) => {
        const remaining = prev.filter((p) => p.id !== id);
        // If deleted project was selected, select first available
        setCurrentId((cur) =>
          cur === id ? (remaining.length > 0 ? remaining[0].id : null) : cur,
        );
        return remaining;
      });
    },
    [],
  );

  // Load projects on mount
  useEffect(() => {
    loadProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <ProjectContext.Provider
      value={{ projects, currentProject, loading, loadProjects, selectProject, createProject, updateProject, deleteProject }}
    >
      {children}
    </ProjectContext.Provider>
  );
}
