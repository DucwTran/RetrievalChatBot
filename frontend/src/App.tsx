import ChatInput from "./components/ChatInput";
import ChatWindow from "./components/ChatWindow";
import Header from "./components/Header";
import { useChat } from "./hooks/useChat";

export default function App() {
  const { messages, loading, error, send, retry, reset } = useChat();

  return (
    <div className="flex h-full flex-col bg-gradient-to-br from-blue-50 to-green-100">
      <Header onNewChat={reset} disabled={loading || messages.length === 0} />
      <ChatWindow messages={messages} loading={loading} error={error} onRetry={retry} />
      <ChatInput onSend={send} disabled={loading} />
    </div>
  );
}
