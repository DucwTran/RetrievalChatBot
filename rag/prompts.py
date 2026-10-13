from collections.abc import Sequence

from llm.base import ChatMessage
from memory.session import Message

NO_ANSWER = (
    "Mình không tìm thấy thông tin về vấn đề này trong dữ liệu hiện tại. "
    "Bạn có thể hỏi mình về các dự án, phong cách nội thất hoặc tin tức của công ty nhé!"
)

SYSTEM_PROMPT = f"""Bạn là trợ lý của công ty kiến trúc - nội thất, tư vấn về dự án, phong cách nội thất, tin tức và thông tin công ty.
Giọng điệu thân thiện, tự nhiên, rõ ràng; dùng tiếng Việt; tối đa 2 emoji; chỉ chào ở lượt đầu tiên của cuộc trò chuyện.

QUY TẮC:
1. Chỉ trả lời dựa trên phần "Ngữ cảnh truy xuất" (Retrieved Context). Không dùng kiến thức bên ngoài, không suy đoán, không bịa.
2. Nếu ngữ cảnh không đủ để trả lời, hãy nói rõ rằng bạn không tìm thấy thông tin, ví dụ: "{NO_ANSWER}"
3. Lịch sử hội thoại chỉ giúp bạn hiểu câu hỏi hiện tại đang nói về chủ đề nào (ví dụ "thế còn diện tích?"). Lịch sử KHÔNG phải nguồn thông tin: mọi dữ kiện phải có trong ngữ cảnh truy xuất.
4. Trình bày có cấu trúc (gạch đầu dòng nếu có nhiều mục), nêu rõ tên khi liệt kê.
"""

REWRITE_PROMPT = """Dựa vào hội thoại dưới đây, hãy viết lại câu hỏi cuối cùng của người dùng thành MỘT câu hỏi độc lập, đầy đủ ngữ cảnh, để có thể tìm kiếm mà không cần xem hội thoại. Giữ nguyên ngôn ngữ. KHÔNG trả lời câu hỏi. Chỉ in ra câu hỏi đã viết lại.

Hội thoại:
{history}

Câu hỏi cuối cùng: {question}

Câu hỏi độc lập:"""


def format_history(history: Sequence[Message]) -> str:
    return "\n".join(f"{'Người dùng' if m.role == 'user' else 'Trợ lý'}: {m.content}" for m in history)


def build_messages(history: Sequence[Message], context: str, question: str) -> list[ChatMessage]:
    """system -> prior turns -> (retrieved context + current question)."""
    messages = [ChatMessage("system", SYSTEM_PROMPT)]
    messages += [ChatMessage(m.role, m.content) for m in history]
    messages.append(
        ChatMessage(
            "user",
            f"Ngữ cảnh truy xuất (Retrieved Context):\n{context}\n\n"
            f"Câu hỏi hiện tại (Current Question): {question}\n\n"
            "Hãy trả lời câu hỏi bằng ngữ cảnh truy xuất ở trên.",
        )
    )
    return messages
