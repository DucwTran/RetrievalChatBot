import { Bot, User } from "lucide-react";
import type { ChatMessage } from "../hooks/useChat";
import SourceList from "./SourceList";

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-green-600">
          <Bot className="h-5 w-5 text-white" />
        </div>
      )}
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser ? "bg-green-600 text-white" : "bg-white text-gray-800 shadow-sm"
        }`}
      >
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
        {!isUser && message.sources && <SourceList sources={message.sources} />}
      </div>
      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-700">
          <User className="h-5 w-5 text-white" />
        </div>
      )}
    </div>
  );
}
