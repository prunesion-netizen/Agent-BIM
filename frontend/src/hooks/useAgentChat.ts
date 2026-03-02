/**
 * useAgentChat.ts — Custom hook pentru agent chat cu SSE streaming.
 *
 * Gestionează:
 * - Fetch SSE stream de la backend
 * - Parsarea event-urilor
 * - State management pentru mesaje și tool steps
 */

import { useState, useRef, useCallback } from "react";
import type {
  AgentMessage,
  ToolStep,
  AgentSSEEvent,
} from "../types/agent";

interface UseAgentChatReturn {
  messages: AgentMessage[];
  isLoading: boolean;
  sendMessage: (text: string) => void;
  clearMessages: () => void;
}

export default function useAgentChat(projectId: number | null): UseAgentChatReturn {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const nextId = useRef(0);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!projectId || isLoading) return;

      // Add user message
      const userMsg: AgentMessage = {
        id: nextId.current++,
        role: "user",
        content: text,
      };

      // Build conversation history from existing messages (text only)
      const history = messages
        .filter((m) => m.role === "user" || m.role === "assistant")
        .map((m) => ({ role: m.role, content: m.content }));

      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      // Prepare assistant message placeholder
      const assistantId = nextId.current++;
      const toolSteps: ToolStep[] = [];
      let fullText = "";

      setMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          role: "assistant",
          content: "",
          toolSteps: [],
        },
      ]);

      // Helper to update the assistant message in state
      const updateAssistant = (content: string, steps: ToolStep[]) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content, toolSteps: [...steps] }
              : m,
          ),
        );
      };

      try {
        abortRef.current = new AbortController();

        const res = await fetch(
          `/api/projects/${projectId}/agent-chat`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              message: text,
              conversation_history: history,
            }),
            signal: abortRef.current.signal,
          },
        );

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
          throw new Error(err.detail || `Eroare server: ${res.status}`);
        }

        const reader = res.body?.getReader();
        if (!reader) throw new Error("Nu se poate citi stream-ul");

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // Parse SSE events from buffer
          const lines = buffer.split("\n");
          buffer = "";

          let currentEventType = "";

          for (let i = 0; i < lines.length; i++) {
            const line = lines[i];

            if (line.startsWith("event: ")) {
              currentEventType = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              const dataStr = line.slice(6);
              try {
                const event = JSON.parse(dataStr) as AgentSSEEvent;
                processEvent(event, toolSteps, (t) => {
                  fullText = t;
                }, fullText);
                updateAssistant(fullText, toolSteps);
              } catch {
                // Incomplete JSON, keep in buffer
                // Reconstruct remaining lines as buffer
                const remaining = lines.slice(i).join("\n");
                if (!remaining.endsWith("\n\n")) {
                  buffer = remaining;
                  break;
                }
              }
            } else if (line === "" && currentEventType) {
              currentEventType = "";
            } else if (line !== "") {
              // Incomplete line, keep in buffer
              buffer = lines.slice(i).join("\n");
              break;
            }
          }
        }
      } catch (e) {
        if ((e as Error).name === "AbortError") return;

        const errorText = `**Eroare:** ${e instanceof Error ? e.message : "Eroare necunoscută"}`;
        fullText = fullText ? fullText + "\n\n" + errorText : errorText;
        updateAssistant(fullText, toolSteps);
      } finally {
        setIsLoading(false);
        abortRef.current = null;
      }
    },
    [projectId, isLoading, messages],
  );

  const clearMessages = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
    }
    setMessages([]);
    setIsLoading(false);
  }, []);

  return { messages, isLoading, sendMessage, clearMessages };
}

function processEvent(
  event: AgentSSEEvent,
  toolSteps: ToolStep[],
  setText: (text: string) => void,
  currentText: string,
) {
  switch (event.type) {
    case "tool_call":
      toolSteps.push({
        call_id: event.call_id,
        tool_name: event.tool_name,
        tool_input: event.tool_input,
        status: "running",
      });
      break;

    case "tool_result": {
      const step = toolSteps.find((s) => s.call_id === event.call_id);
      if (step) {
        step.result = event.result;
        step.duration_ms = event.duration_ms;
        step.status = event.result?.error ? "error" : "completed";
      }
      break;
    }

    case "text_delta":
      setText(currentText ? currentText + event.content : event.content);
      break;

    case "error":
      setText(
        currentText
          ? currentText + "\n\n**Eroare:** " + event.message
          : "**Eroare:** " + event.message,
      );
      break;

    case "done":
      // Nothing to do, stream ends
      break;
  }
}
