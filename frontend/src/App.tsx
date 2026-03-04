import { useState, useCallback, lazy, Suspense } from "react";
import { AuthProvider, useAuth } from "./contexts/AuthProvider";
import { ProjectProvider, useProject } from "./contexts/ProjectProvider";
import { ToastProvider } from "./components/Toast";
import LoginPage from "./components/LoginPage";
import ProjectSelector from "./components/ProjectSelector";
import NotificationBell from "./components/NotificationBell";
import Dashboard from "./components/Dashboard";
import ProjectContextFormDemo from "./components/ProjectContextFormDemo";
import ChatExpert from "./components/ChatExpert";
import AgentChat from "./components/AgentChat";
import BepVerifier from "./components/BepVerifier";
import ComplianceDashboard from "./components/ComplianceDashboard";
import DeliveryPlan from "./components/DeliveryPlan";
import EirPanel from "./components/EirPanel";
import RaciMatrix from "./components/RaciMatrix";
import LoinMatrix from "./components/LoinMatrix";
import HandoverChecklist from "./components/HandoverChecklist";
import ClashManager from "./components/ClashManager";
import KpiDashboard from "./components/KpiDashboard";
import CobieValidator from "./components/CobieValidator";

const IfcViewer = lazy(() => import("./components/IfcViewer"));

type Tab = "dashboard" | "bep" | "agent" | "chat" | "verifier" | "viewer" | "conformitate";
type ConformitateSubView = "compliance" | "eir" | "tidp" | "raci" | "loin" | "handover" | "clash" | "kpi" | "cobie";

export interface BepContext {
  projectCode: string;
  projectName: string;
  bepMarkdown: string;
}

function AppContent() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [subView, setSubView] = useState<ConformitateSubView>("compliance");
  const [bepCtx, setBepCtx] = useState<BepContext | null>(null);
  const { currentProject, selectProject } = useProject();
  const { user, logout } = useAuth();

  const handleBepGenerated = useCallback((ctx: BepContext) => {
    setBepCtx(ctx);
  }, []);

  const goToChat = useCallback(() => {
    setTab("chat");
  }, []);

  const handleDashboardSelect = useCallback(
    (projectId: number, targetTab: "bep" | "agent" | "chat" | "verifier" | "viewer") => {
      selectProject(projectId);
      setTab(targetTab);
    },
    [selectProject],
  );

  return (
    <div className="app-shell">
      {/* ── Top bar: user info ── */}
      {user && (
        <div className="app-topbar">
          <span className="app-topbar-brand">Agent BIM</span>
          <div className="app-topbar-right">
            <ProjectSelector />
            <NotificationBell />
            <span className="user-badge">
              {user.username}
              <span className="user-badge-role">({user.role})</span>
            </span>
            <button className="logout-btn" onClick={logout}>
              Logout
            </button>
          </div>
        </div>
      )}

      {/* ── Tab navigation ── */}
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
          <button
            className={`app-tab ${tab === "conformitate" ? "active" : ""}`}
            onClick={() => setTab("conformitate")}
          >
            <span className="app-tab-icon">&#9878;</span>
            Conformitate
            {currentProject && <span className="app-tab-badge" />}
          </button>
          <button
            className={`app-tab ${tab === "viewer" ? "active" : ""}`}
            onClick={() => setTab("viewer")}
          >
            <span className="app-tab-icon">&#9635;</span>
            Viewer 3D
            {currentProject && <span className="app-tab-badge" />}
          </button>
        </div>
      </nav>

      {/* ── Sub-navigation for Conformitate ── */}
      {tab === "conformitate" && (
        <nav className="app-subtabs">
          {([
            ["compliance", "ISO Compliance"],
            ["eir", "EIR"],
            ["tidp", "TIDP/MIDP"],
            ["raci", "RACI"],
            ["loin", "LOIN"],
            ["handover", "Handover"],
            ["clash", "Clash-uri"],
            ["kpi", "KPI"],
            ["cobie", "COBie"],
          ] as [ConformitateSubView, string][]).map(([key, label]) => (
            <button
              key={key}
              className={`app-subtab ${subView === key ? "active" : ""}`}
              onClick={() => setSubView(key)}
            >
              {label}
            </button>
          ))}
        </nav>
      )}

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
        {tab === "conformitate" && (
          <>
            {subView === "compliance" && <ComplianceDashboard />}
            {subView === "eir" && <EirPanel />}
            {subView === "tidp" && <DeliveryPlan />}
            {subView === "raci" && <RaciMatrix />}
            {subView === "loin" && <LoinMatrix />}
            {subView === "handover" && <HandoverChecklist />}
            {subView === "clash" && <ClashManager />}
            {subView === "kpi" && <KpiDashboard />}
            {subView === "cobie" && <CobieValidator />}
          </>
        )}
        {tab === "viewer" && (
          <Suspense fallback={<div className="loading-center"><div className="spinner spinner-dark spinner-lg" /><span>Se incarca Viewer 3D...</span></div>}>
            <IfcViewer projectId={currentProject?.id ?? null} />
          </Suspense>
        )}
      </main>
    </div>
  );
}

function AuthGate() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-center" style={{ minHeight: "100vh" }}>
        <div className="spinner spinner-dark spinner-lg" />
        <span>Se incarca...</span>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  return (
    <ProjectProvider>
      <AppContent />
    </ProjectProvider>
  );
}

function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <AuthGate />
      </AuthProvider>
    </ToastProvider>
  );
}

export default App;
