import { useState } from "react";
import ProjectContextFormDemo from "./components/ProjectContextFormDemo";
import ChatExpert from "./components/ChatExpert";

type Tab = "bep" | "chat";

function App() {
  const [tab, setTab] = useState<Tab>("bep");

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
        </button>
      </nav>

      <main className="app-main">
        {tab === "bep" && <ProjectContextFormDemo />}
        {tab === "chat" && <ChatExpert />}
      </main>
    </div>
  );
}

export default App;
