import { useState, useRef, useEffect, type FormEvent } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
}

const SUGGESTIONS = [
  "Ce este un BEP conform ISO 19650-2?",
  "Care sunt rolurile intr-o echipa BIM?",
  "Cum se structureaza un CDE?",
  "Ce inseamna LOD 300 vs LOD 350?",
  "Cum functioneaza clash detection?",
  "Care sunt fazele unui proiect BIM in Romania?",
];

export default function ChatExpert() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  let nextId = useRef(0);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  async function sendMessage(text: string) {
    const userMsg: Message = { id: nextId.current++, role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat-expert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, project_id: null }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(err.detail || `Eroare server: ${res.status}`);
      }

      const data = await res.json();
      const assistantMsg: Message = {
        id: nextId.current++,
        role: "assistant",
        content: data.answer,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e) {
      const errorMsg: Message = {
        id: nextId.current++,
        role: "assistant",
        content: `**Eroare:** ${e instanceof Error ? e.message : "Eroare necunoscuta"}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    sendMessage(text);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  const isEmpty = messages.length === 0;

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {isEmpty && !loading && (
          <div className="chat-welcome">
            <div className="chat-welcome-icon">BIM</div>
            <h2>Expert BIM Romania</h2>
            <p>
              Intreaba orice despre BIM, ISO 19650, CDE, LOD, clash detection,
              standarde romanesti (RTC 8/9) sau bune practici de proiectare.
            </p>
            <div className="chat-suggestions">
              {SUGGESTIONS.map((s) => (
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
            <div className="chat-msg-avatar">
              {msg.role === "user" ? "Tu" : "AI"}
            </div>
            <div className="chat-msg-body">
              {msg.role === "assistant" ? (
                <div className="chat-md">
                  <Markdown remarkPlugins={[remarkGfm]}>{msg.content}</Markdown>
                </div>
              ) : (
                <p>{msg.content}</p>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="chat-msg chat-msg-assistant">
            <div className="chat-msg-avatar">AI</div>
            <div className="chat-msg-body">
              <div className="chat-typing">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <form className="chat-input-bar" onSubmit={handleSubmit}>
        <textarea
          ref={inputRef}
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Intreaba Expert BIM..."
          rows={1}
          disabled={loading}
        />
        <button
          type="submit"
          className="chat-send-btn"
          disabled={!input.trim() || loading}
        >
          Trimite
        </button>
      </form>
    </div>
  );
}
