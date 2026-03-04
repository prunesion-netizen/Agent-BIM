/**
 * AgentChat.tsx — Componenta principală Agent BIM chat cu sidebar conversații.
 *
 * Afișează: sidebar cu istoric conversații, mesaje, tool call cards, sugestii, input.
 * UX: copy-to-clipboard, auto-resize textarea, context bar îmbunătățit.
 */

import { useState, useRef, useEffect, useCallback, type FormEvent } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import StatusBadge from "./StatusBadge";
import ToolCallCard from "./ToolCallCard";
import ConfirmDialog from "./ConfirmDialog";
import useAgentChat from "../hooks/useAgentChat";

interface Props {
  projectId: number | null;
  projectStatus: string | null;
  projectName?: string;
  projectCode?: string;
}

const SUGGESTIONS_NEW = [
  "Care este statusul proiectului?",
  "Ce trebuie sa fac pentru a genera un BEP?",
  "Explica-mi ce este un BEP conform ISO 19650",
  "Verifica sanatatea proiectului",
];

const SUGGESTIONS_CONTEXT = [
  "Genereaza BEP-ul proiectului",
  "Arata-mi fisa BEP a proiectului",
  "Ce discipline sunt definite in proiect?",
  "Verifica sanatatea proiectului",
];

const SUGGESTIONS_BEP = [
  "Verifica BEP-ul fata de model",
  "Exporta BEP-ul ca DOCX",
  "Compara versiunile BEP",
  "Analizeaza modelul IFC",
];

const SUGGESTIONS_VERIFIED = [
  "Ce neconformitati a gasit ultima verificare?",
  "Arata istoricul verificarilor",
  "Arata jurnalul de activitati",
  "Compara versiunile BEP",
];

function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("ro-RO", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function AgentChat({
  projectId,
  projectStatus,
  projectName,
  projectCode,
}: Props) {
  const {
    messages,
    isLoading,
    conversationId,
    conversations,
    sendMessage,
    clearMessages,
    loadConversation,
    startNewConversation,
    deleteConversation,
  } = useAgentChat(projectId);
  const [input, setInput] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Auto-resize textarea (max 4 linii)
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const textarea = e.target;
    textarea.style.height = "auto";
    const maxHeight = parseInt(getComputedStyle(textarea).lineHeight) * 4 + 16;
    textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`;
  }, []);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || isLoading) return;
    setInput("");
    // Reset textarea height
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
    }
    sendMessage(text);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  function handleDeleteConversation(e: React.MouseEvent, convId: number) {
    e.stopPropagation();
    setDeleteTarget(convId);
  }

  async function handleCopyMessage(msgId: number, content: string) {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedId(msgId);
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      // fallback
    }
  }

  const isEmpty = messages.length === 0;
  const suggestions =
    projectStatus?.startsWith("bep_verified")
      ? SUGGESTIONS_VERIFIED
      : projectStatus === "bep_generated"
        ? SUGGESTIONS_BEP
        : projectStatus === "context_defined"
          ? SUGGESTIONS_CONTEXT
          : SUGGESTIONS_NEW;

  if (!projectId) {
    return (
      <div className="chat-container">
        <div className="chat-welcome">
          <div className="chat-welcome-icon">BIM</div>
          <h2>Agent BIM Romania</h2>
          <p>Selecteaza un proiect din meniul de mai sus pentru a incepe.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="agent-layout">
      {/* Confirm delete conversation */}
      <ConfirmDialog
        open={deleteTarget !== null}
        title="Sterge conversatia"
        message="Sigur doriti sa stergeti aceasta conversatie? Istoricul va fi pierdut."
        confirmLabel="Sterge"
        danger
        onCancel={() => setDeleteTarget(null)}
        onConfirm={() => {
          if (deleteTarget !== null) {
            deleteConversation(deleteTarget);
            setDeleteTarget(null);
          }
        }}
      />

      {/* Sidebar conversații */}
      <div className={`agent-sidebar ${sidebarOpen ? "open" : "closed"}`}>
        <div className="agent-sidebar-header">
          <span className="agent-sidebar-title">Conversatii</span>
          <button
            className="agent-sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            title={sidebarOpen ? "Ascunde sidebar" : "Arata sidebar"}
            aria-label={sidebarOpen ? "Ascunde sidebar conversatii" : "Arata sidebar conversatii"}
          >
            {sidebarOpen ? "\u2039" : "\u203A"}
          </button>
        </div>

        {sidebarOpen && (
          <>
            <button
              className="agent-new-conv-btn"
              onClick={startNewConversation}
            >
              + Conversatie noua
            </button>

            <div className="agent-sidebar-list">
              {conversations.length === 0 && (
                <p className="agent-sidebar-empty">
                  Nicio conversatie salvata.
                </p>
              )}
              {conversations.map((c) => (
                <div
                  key={c.id}
                  className={`agent-sidebar-item ${
                    c.id === conversationId ? "active" : ""
                  }`}
                  onClick={() => loadConversation(c.id)}
                >
                  <div className="agent-sidebar-item-title">{c.title}</div>
                  <div className="agent-sidebar-item-meta">
                    {c.message_count} mesaje &middot; {formatDate(c.updated_at)}
                  </div>
                  <button
                    className="agent-sidebar-item-delete"
                    onClick={(e) => handleDeleteConversation(e, c.id)}
                    title="Sterge conversatia"
                    aria-label="Sterge aceasta conversatie"
                  >
                    &times;
                  </button>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Chat principal */}
      <div className="chat-container">
        {/* Context bar îmbunătățit */}
        <div className="chat-context-bar">
          <span className="chat-context-dot" />
          Agent activ pentru:{" "}
          <strong>{projectName || `Proiect #${projectId}`}</strong>
          {projectCode && ` (${projectCode})`}
          {projectStatus && <StatusBadge status={projectStatus} />}
          <span className="chat-context-tools">13 tool-uri</span>
          {!sidebarOpen && (
            <button
              className="agent-sidebar-toggle-inline"
              onClick={() => setSidebarOpen(true)}
              title="Arata conversatii"
              aria-label="Deschide panoul de conversatii"
            >
              Conversatii
            </button>
          )}
          <button
            className="agent-clear-btn"
            onClick={clearMessages}
            title="Conversatie noua"
          >
            Conversatie noua
          </button>
        </div>

        {/* Messages area */}
        <div className="chat-messages">
          {isEmpty && !isLoading && (
            <div className="chat-welcome">
              <div className="chat-welcome-icon">BIM</div>
              <h2>Agent BIM Romania</h2>
              <p>
                Agentul autonom poate genera BEP-uri, verifica conformitatea,
                analiza modele IFC, compara versiuni, exporta documente si
                raspunde la intrebari despre standardele BIM.
                Spune-i ce vrei sa faca.
              </p>
              <div className="chat-suggestions">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    className="chat-suggestion"
                    onClick={() => sendMessage(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={`chat-msg chat-msg-${msg.role}`}>
              {msg.role !== "system" && (
                <div className="chat-msg-avatar">
                  {msg.role === "user" ? "Tu" : "AI"}
                </div>
              )}
              <div className="chat-msg-body">
                {/* Tool steps */}
                {msg.toolSteps && msg.toolSteps.length > 0 && (
                  <div className="tool-steps-container">
                    {msg.toolSteps.map((step) => (
                      <ToolCallCard key={step.call_id} step={step} />
                    ))}
                  </div>
                )}

                {/* Text content */}
                {msg.role === "assistant" && msg.content ? (
                  <div className="chat-md">
                    <Markdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </Markdown>
                    {/* Copy to clipboard button */}
                    <button
                      className="chat-copy-btn"
                      onClick={() => handleCopyMessage(msg.id, msg.content)}
                      title="Copiaza mesajul"
                      aria-label="Copiaza mesajul in clipboard"
                    >
                      {copiedId === msg.id ? "\u2713 Copiat" : "Copiaza"}
                    </button>
                  </div>
                ) : msg.role === "system" ? (
                  <div className="chat-system-msg">
                    <Markdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </Markdown>
                  </div>
                ) : msg.role === "user" ? (
                  <p>{msg.content}</p>
                ) : null}
              </div>
            </div>
          ))}

          {isLoading &&
            messages.length > 0 &&
            !messages[messages.length - 1]?.toolSteps?.length &&
            !messages[messages.length - 1]?.content && (
              <div className="chat-msg chat-msg-assistant">
                <div className="chat-msg-avatar">AI</div>
                <div className="chat-msg-body">
                  <div className="chat-typing">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}

          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <form className="chat-input-bar" onSubmit={handleSubmit}>
          <textarea
            ref={inputRef}
            className="chat-input"
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={
              projectCode
                ? `Spune agentului ce sa faca pentru ${projectCode}...`
                : "Scrie un mesaj..."
            }
            rows={1}
            disabled={isLoading}
          />
          <button
            type="submit"
            className="chat-send-btn"
            disabled={!input.trim() || isLoading}
          >
            Trimite
          </button>
        </form>
      </div>
    </div>
  );
}
