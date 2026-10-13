import { MessageSquarePlus } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../lib/api";

type Status = "checking" | "ok" | "degraded" | "down";

const DOT: Record<Status, string> = {
  checking: "bg-gray-300",
  ok: "bg-green-500",
  degraded: "bg-amber-500",
  down: "bg-red-500",
};

const LABEL: Record<Status, string> = {
  checking: "Đang kiểm tra",
  ok: "Sẵn sàng",
  degraded: "Một phần dịch vụ lỗi",
  down: "Mất kết nối",
};

export default function Header({ onNewChat, disabled }: { onNewChat: () => void; disabled: boolean }) {
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    let active = true;
    const poll = async () => {
      const health = await api.health();
      if (active) setStatus(health ? health.status : "down");
    };
    void poll();
    const timer = setInterval(poll, 30_000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, []);

  return (
    <header className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3">
      <div>
        <h1 className="text-lg font-semibold text-gray-800">Trợ lý RAG</h1>
        <p className="flex items-center gap-1.5 text-xs text-gray-500">
          <span className={`h-2 w-2 rounded-full ${DOT[status]}`} />
          {LABEL[status]}
        </p>
      </div>
      <button
        onClick={onNewChat}
        disabled={disabled}
        className="flex items-center gap-1.5 rounded-full border border-gray-300 px-3 py-1.5 text-sm text-gray-700 transition hover:bg-gray-50 disabled:opacity-50"
      >
        <MessageSquarePlus className="h-4 w-4" />
        Cuộc trò chuyện mới
      </button>
    </header>
  );
}
