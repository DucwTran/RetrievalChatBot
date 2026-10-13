import { Send } from "lucide-react";
import { useState, type FormEvent, type KeyboardEvent } from "react";

// Keep in sync with API__MAX_MESSAGE_LENGTH on the backend.
const MAX_LENGTH = Number(import.meta.env.VITE_MAX_MESSAGE_LENGTH ?? 500);

export default function ChatInput({ onSend, disabled }: { onSend: (text: string) => void; disabled: boolean }) {
  const [text, setText] = useState("");
  const canSend = !disabled && text.trim().length > 0;

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    if (!canSend) return;
    onSend(text);
    setText("");
  };

  // Enter sends, Shift+Enter inserts a newline.
  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <form onSubmit={submit} className="border-t border-gray-200 bg-white px-4 py-3">
      <div className="mx-auto flex max-w-3xl items-end gap-2">
        <div className="flex-1">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={onKeyDown}
            maxLength={MAX_LENGTH}
            rows={1}
            placeholder="Nhập câu hỏi của bạn..."
            className="max-h-32 w-full resize-none rounded-2xl border border-gray-300 px-4 py-3 text-gray-800 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          {text.length > MAX_LENGTH * 0.8 && (
            <p className="mt-1 text-right text-xs text-gray-400">
              {text.length}/{MAX_LENGTH}
            </p>
          )}
        </div>
        <button
          type="submit"
          disabled={!canSend}
          aria-label="Gửi"
          className="flex h-12 items-center gap-2 rounded-full bg-green-600 px-5 text-white transition hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-gray-300"
        >
          <Send className="h-5 w-5" />
          Gửi
        </button>
      </div>
    </form>
  );
}
