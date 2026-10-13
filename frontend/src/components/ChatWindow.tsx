import { useEffect, useRef } from "react";
import type { ChatMessage } from "../hooks/useChat";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";

interface Props {
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

export default function ChatWindow({ messages, loading, error, onRetry }: Props) {
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, error]);

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-3xl space-y-4 px-4 py-6">
        {messages.length === 0 && (
          <div className="py-12 text-center">
            <h2 className="mb-2 text-xl font-semibold text-gray-700">Xin chào! Tôi có thể giúp gì cho bạn?</h2>
            <p className="text-gray-500">Hỏi tôi về dự án, phong cách nội thất, tin tức hoặc thông tin công ty.</p>
          </div>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        {loading && <TypingIndicator />}
        {error && (
          <div role="alert" className="flex items-center justify-between gap-3 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            <span>{error}</span>
            <button onClick={onRetry} disabled={loading} className="font-medium underline disabled:opacity-50">
              Thử lại
            </button>
          </div>
        )}
        <div ref={bottom} />
      </div>
    </div>
  );
}
