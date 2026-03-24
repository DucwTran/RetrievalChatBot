import logging
import os

from core.load_settings import load_settings
from retrieval.retriever import retrieve
from llm.generator import generate_answer

settings = load_settings()
logger = logging.getLogger("chat")

MAX_QUERY_LENGTH = int(os.getenv("MAX_QUERY_LENGTH", "512"))

def chat(question: str) -> str:
    if not question:
        logger.warning("Received empty question.")
        return "Câu hỏi không được để trống. Vui lòng nhập câu hỏi của bạn."

    if len(question) > MAX_QUERY_LENGTH:
        logger.warning("Question length exceeds maximum limit.")
        return f"Câu hỏi vượt quá độ dài tối đa cho phép là {MAX_QUERY_LENGTH} ký tự."

    logger.info(f"Starting retrieval for the question: {question}.")

    try:
        documents = retrieve(question)
        if not documents:
            logger.info("No relevant documents found.")
            return "Tôi không tìm thấy thông tin phù hợp trong dữ liệu hiện có."

        # [1] Noi dung context 1
        # {Nguon: {}}

        # [2] Noi dung context 2
        # {Nguon: {}}

        context = "\n\n".join(
            f"[{i+1}] {doc.text}\n(Nguồn: {doc.metadata})"
            for i, doc in enumerate(documents)
        )

        answer = generate_answer(context, question)
        logger.info("Answer generated successfully.")
        return answer

    except Exception as e:
        logger.error(f"Exception during retrieval: {e}")
        return "Đã xảy ra lỗi trong quá trình truy xuất thông tin. Vui lòng thử lại sau."
    
def main():
    while True:
        question = input("Bạn: ")
        if question.lower() in {"exit", "quit"}:
            print("Kết thúc cuộc trò chuyện.")
            break
            
        answer = chat(question)
        print(f"Bot: {answer}")

if __name__ == "__main__":
    main()