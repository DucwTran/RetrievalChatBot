const API_URL: string = import.meta.env.VITE_API_URL ?? "";

export interface Source {
  title: string;
  type: string | null;
  slug: string | null;
  image_url: string | null;
  snippet: string;
  score: number;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  sources: Source[];
}

export interface Health {
  status: "ok" | "degraded";
  llm: { status: string; provider: string; model: string };
}

/** Error with the HTTP status and the backend's machine-readable code (see ErrorResponse). */
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

const FRIENDLY: Record<string, string> = {
  invalid_request: "Câu hỏi không hợp lệ. Hãy kiểm tra lại nội dung.",
  rate_limited: "Bạn gửi quá nhanh, vui lòng thử lại sau ít phút.",
  vector_store_unavailable: "Cơ sở dữ liệu tri thức đang không khả dụng.",
  llm_unavailable: "Mô hình ngôn ngữ đang không khả dụng.",
  llm_timeout: "Mô hình trả lời quá lâu, vui lòng thử lại.",
  llm_error: "Mô hình gặp lỗi khi tạo câu trả lời.",
  network: "Không kết nối được tới máy chủ.",
};

export function describeError(error: unknown): string {
  if (error instanceof ApiError) return FRIENDLY[error.code] ?? error.message;
  return "Đã xảy ra lỗi, vui lòng thử lại.";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, init);
  } catch {
    throw new ApiError(0, "network", FRIENDLY.network);
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(response.status, body?.error ?? "unknown", body?.message ?? response.statusText);
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}

export const api = {
  chat: (message: string, sessionId?: string) =>
    request<ChatResponse>("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    }),

  clearSession: (sessionId: string) => request<void>(`/sessions/${sessionId}`, { method: "DELETE" }),

  // /health answers 503 when degraded but still returns a body worth showing.
  health: async (): Promise<Health | null> => {
    try {
      return (await (await fetch(`${API_URL}/health`)).json()) as Health;
    } catch {
      return null;
    }
  },
};
