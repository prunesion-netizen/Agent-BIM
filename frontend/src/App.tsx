import { useState, useCallback } from "react";
import { ProjectProvider, useProject } from "./contexts/ProjectProvider";
import ProjectSelector from "./components/ProjectSelector";
import ProjectContextFormDemo from "./components/ProjectContextFormDemo";
import ChatExpert from "./components/ChatExpert";
import BepVerifier from "./components/BepVerifier";

type Tab = "bep" | "chat" | "verifier";

export interface BepContext {
  projectCode: string;
  projectName: string;
  bepMarkdown: string;
}

function AppContent() {
  const [tab, setTab] = useState<Tab>("bep");
  const [bepCtx, setBepCtx] = useState<BepContext | null>(null);
  const { currentProject } = useProject();

  const handleBepGenerated = useCallback((ctx: BepContext) => {
    setBepCtx(ctx);
  }, []);

  const goToChat = useCallback(() => {
    setTab("chat");
  }, []);

  return (
    <div className="app-shell">
      <nav className="app-tabs">
        <div className="app-tabs-left">
          <button
            className={`app-tab ${tab === "bep" ? "active" : ""}`}
            onClick={() => setTab("bep")}
          >
            <span className="app-tab-icon">&#9776;</span>
            Fisa BEP
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
        {tab === "bep" && (
          <ProjectContextFormDemo
            onBepGenerated={handleBepGenerated}
            onGoToChat={goToChat}
          />
        )}
        {tab === "chat" && (
          <ChatExpert
            bepContext={bepCtx}
            projectId={currentProject?.id ?? null}
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
