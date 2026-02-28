import { useState, useCallback } from "react";
import ProjectContextFormDemo from "./components/ProjectContextFormDemo";
import ChatExpert from "./components/ChatExpert";

type Tab = "bep" | "chat";

export interface BepContext {
  projectCode: string;
  projectName: string;
  bepMarkdown: string;
}

function App() {
  const [tab, setTab] = useState<Tab>("bep");
  const [bepCtx, setBepCtx] = useState<BepContext | null>(null);

  const handleBepGenerated = useCallback((ctx: BepContext) => {
    setBepCtx(ctx);
  }, []);

  const goToChat = useCallback(() => {
    setTab("chat");
  }, []);

  return (
    <div className="app-shell">
      <nav className="app-tabs">
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
      </nav>

      <main className="app-main">
        {tab === "bep" && (
          <ProjectContextFormDemo
            onBepGenerated={handleBepGenerated}
            onGoToChat={goToChat}
          />
        )}
        {tab === "chat" && (
          <ChatExpert bepContext={bepCtx} />
        )}
      </main>
    </div>
  );
}

export default App;
