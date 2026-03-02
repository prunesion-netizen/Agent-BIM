/**
 * AgentChat.tsx — Componenta principală Agent BIM chat.
 *
 * Afișează: mesaje, tool call cards, sugestii, input.
 */

import { useState, useRef, useEffect, type FormEvent } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import StatusBadge from "./StatusBadge";
import ToolCallCard from "./ToolCallCard";
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
];

const SUGGESTIONS_CONTEXT = [
  "Genereaza BEP-ul proiectului",
  "Arata-mi fisa BEP a proiectului",
  "Ce discipline sunt definite in proiect?",
];

const SUGGESTIONS_BEP = [
  "Verifica BEP-ul fata de model",
  "Exporta BEP-ul ca DOCX",
  "Rezuma capitolele principale din BEP",
];

const SUGGESTIONS_VERIFIED = [
  "Ce neconformitati a gasit ultima verificare?",
  "Arata istoricul verificarilor",
  "Cum rezolv problemele gasite?",
  "Exporta BEP-ul ca DOCX",
];

export default function AgentChat({
  projectId,
  projectStatus,
  projectName,
  projectCode,
}: Props) {
  const { messages, isLoading, sendMessage, clearMessages } =
    useAgentChat(projectId);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || isLoading) return;
    setInput("");
    sendMessage(text);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
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
    <div className="chat-container">
      {/* Context bar */}
      <div className="chat-context-bar">
        <span className="chat-context-dot" />
        Agent activ pentru:{" "}
        <strong>{projectName || `Proiect #${projectId}`}</strong>
        {projectCode && ` (${projectCode})`}
        {projectStatus && <StatusBadge status={projectStatus} />}
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
              exporta documente si raspunde la intrebari despre standardele BIM.
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
          onChange={(e) => setInput(e.target.value)}
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
  );
}
