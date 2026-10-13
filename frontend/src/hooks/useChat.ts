import { useCallback, useRef, useState } from "react";
import { api, describeError, type Source } from "../lib/api";

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

const SESSION_KEY = "chat_session_id";

// localStorage can throw (private mode, blocked storage); the chat must still work without it.
function loadSession(): string | undefined {
  try {
    return localStorage.getItem(SESSION_KEY) ?? undefined;
  } catch {
    return undefined;
  }
}

function saveSession(id: string | undefined) {
  try {
    if (id) localStorage.setItem(SESSION_KEY, id);
    else localStorage.removeItem(SESSION_KEY);
  } catch {
    /* ignore */
  }
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sessionId = useRef<string | undefined>(loadSession());
  const nextId = useRef(1);
  const lastQuestion = useRef<string | null>(null);

  const ask = useCallback(async (text: string) => {
    setError(null);
    setLoading(true);
    try {
      const reply = await api.chat(text, sessionId.current);
      sessionId.current = reply.session_id;
      saveSession(reply.session_id);
      setMessages((m) => [
        ...m,
        { id: nextId.current++, role: "assistant", content: reply.answer, sources: reply.sources },
      ]);
      lastQuestion.current = null;
    } catch (e) {
      lastQuestion.current = text; // keep it so the user can retry
      setError(describeError(e));
    } finally {
      setLoading(false);
    }
  }, []);

  const send = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || loading) return;
      setMessages((m) => [...m, { id: nextId.current++, role: "user", content: trimmed }]);
      void ask(trimmed);
    },
    [ask, loading],
  );

  const retry = useCallback(() => {
    if (lastQuestion.current && !loading) void ask(lastQuestion.current);
  }, [ask, loading]);

  const reset = useCallback(async () => {
    const id = sessionId.current;
    sessionId.current = undefined;
    saveSession(undefined);
    setMessages([]);
    setError(null);
    lastQuestion.current = null;
    if (id) await api.clearSession(id).catch(() => undefined); // best effort: memory also expires server-side
  }, []);

  return { messages, loading, error, send, retry, reset };
}
