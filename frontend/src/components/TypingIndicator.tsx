import { Bot } from "lucide-react";

export default function TypingIndicator() {
  return (
    <div className="flex gap-3" role="status" aria-label="Trợ lý đang trả lời">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-green-600">
        <Bot className="h-5 w-5 text-white" />
      </div>
      <div className="flex items-center gap-1 rounded-2xl bg-white px-4 py-3 shadow-sm">
        {[0, 150, 300].map((delay) => (
          <span
            key={delay}
            className="h-2 w-2 animate-bounce rounded-full bg-gray-400"
            style={{ animationDelay: `${delay}ms` }}
          />
        ))}
      </div>
    </div>
  );
}
