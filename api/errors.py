import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.schemas import ErrorResponse
from core.errors import (
    AppError, LLMError, LLMTimeout, LLMUnavailable, RateLimited, RerankerUnavailable, VectorStoreUnavailable,
)

logger = logging.getLogger("api")

# (status, code, user-facing message); most specific class first.
ERROR_MAP: list[tuple[type[Exception], int, str, str]] = [
    (RateLimited, 429, "rate_limited", "Bạn gửi quá nhanh, vui lòng thử lại sau ít phút."),
    (VectorStoreUnavailable, 503, "vector_store_unavailable", "Cơ sở dữ liệu tri thức đang không khả dụng."),
    (RerankerUnavailable, 503, "reranker_unavailable", "Dịch vụ xếp hạng đang không khả dụng."),
    (LLMUnavailable, 503, "llm_unavailable", "Mô hình ngôn ngữ đang không khả dụng."),
    (LLMTimeout, 504, "llm_timeout", "Mô hình trả lời quá lâu, vui lòng thử lại."),
    (LLMError, 502, "llm_error", "Mô hình gặp lỗi khi tạo câu trả lời."),
]


def _response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content=ErrorResponse(error=code, message=message).model_dump())


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return _response(400, "invalid_request", "Yêu cầu không hợp lệ: kiểm tra session_id và nội dung câu hỏi.")

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        for exc_type, status, code, message in ERROR_MAP:
            if isinstance(exc, exc_type):
                logger.warning(f"{code}: {exc}")
                return _response(status, code, message)
        logger.error(f"Unmapped AppError: {exc}", exc_info=True)
        return _response(500, "internal_error", "Đã xảy ra lỗi, vui lòng thử lại sau.")

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error: {exc}", exc_info=True)
        return _response(500, "internal_error", "Đã xảy ra lỗi, vui lòng thử lại sau.")
