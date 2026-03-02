import { useState, useCallback } from "react";
import { ProjectProvider, useProject } from "./contexts/ProjectProvider";
import ProjectSelector from "./components/ProjectSelector";
import Dashboard from "./components/Dashboard";
import ProjectContextFormDemo from "./components/ProjectContextFormDemo";
import ChatExpert from "./components/ChatExpert";
import AgentChat from "./components/AgentChat";
import BepVerifier from "./components/BepVerifier";

type Tab = "dashboard" | "bep" | "agent" | "chat" | "verifier";

export interface BepContext {
  projectCode: string;
  projectName: string;
  bepMarkdown: string;
}

function AppContent() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [bepCtx, setBepCtx] = useState<BepContext | null>(null);
  const { currentProject, selectProject } = useProject();

  const handleBepGenerated = useCallback((ctx: BepContext) => {
    setBepCtx(ctx);
  }, []);

  const goToChat = useCallback(() => {
    setTab("chat");
  }, []);

  const handleDashboardSelect = useCallback(
    (projectId: number, targetTab: "bep" | "agent" | "chat" | "verifier") => {
      selectProject(projectId);
      setTab(targetTab);
    },
    [selectProject],
  );

  return (
    <div className="app-shell">
      <nav className="app-tabs">
        <div className="app-tabs-left">
          <button
            className={`app-tab ${tab === "dashboard" ? "active" : ""}`}
            onClick={() => setTab("dashboard")}
          >
            <span className="app-tab-icon">&#9638;</span>
            Dashboard
          </button>
          <button
            className={`app-tab ${tab === "bep" ? "active" : ""}`}
            onClick={() => setTab("bep")}
          >
            <span className="app-tab-icon">&#9776;</span>
            Fisa BEP
          </button>
          <button
            className={`app-tab ${tab === "agent" ? "active" : ""}`}
            onClick={() => setTab("agent")}
          >
            <span className="app-tab-icon">&#9881;</span>
            Agent BIM
            {currentProject && <span className="app-tab-badge" />}
          </button>
          <button
            className={`app-tab ${tab === "chat" ? "active" : ""}`}
            onClick={() => setTab("chat")}
          >
            <span className="app-tab-icon">&#9993;</span>
            Chat Expert BIM
            {bepCtx && <span className="app-tab-badge" />}
          </button>
          <button
            className={`app-tab ${tab === "verifier" ? "active" : ""}`}
            onClick={() => setTab("verifier")}
          >
            <span className="app-tab-icon">&#9989;</span>
            Verificare BEP
            {bepCtx && <span className="app-tab-badge" />}
          </button>
        </div>

        <div className="app-tabs-right">
          <ProjectSelector />
        </div>
      </nav>

      <main className="app-main">
        {tab === "dashboard" && (
          <Dashboard onSelectProject={handleDashboardSelect} />
        )}
        {tab === "bep" && (
          <ProjectContextFormDemo
            onBepGenerated={handleBepGenerated}
            onGoToChat={goToChat}
          />
        )}
        {tab === "agent" && (
          <AgentChat
            projectId={currentProject?.id ?? null}
            projectStatus={currentProject?.status ?? null}
            projectName={currentProject?.name}
            projectCode={currentProject?.code}
          />
        )}
        {tab === "chat" && (
          <ChatExpert
            bepContext={bepCtx}
            projectId={currentProject?.id ?? null}
            projectStatus={currentProject?.status ?? null}
          />
        )}
        {tab === "verifier" && (
          <BepVerifier
            bepContext={bepCtx}
            projectId={currentProject?.id ?? null}
          />
        )}
      </main>
    </div>
  );
}

function App() {
  return (
    <ProjectProvider>
      <AppContent />
    </ProjectProvider>
  );
}

export default App;
