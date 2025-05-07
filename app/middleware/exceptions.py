"""
Custom exceptions and error handling for the FAQ Pipeline API.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

# Configure logging
logger = logging.getLogger("faq_pipeline.exceptions")

class FAQProcessingError(Exception):
    """Base exception for FAQ pipeline processing errors."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class FileFormatError(FAQProcessingError):
    """Exception for file format errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class ResourceNotFoundError(FAQProcessingError):
    """Exception for resource not found errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)

class ExtractionError(FAQProcessingError):
    """Exception for FAQ extraction errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)

class DatabaseError(FAQProcessingError):
    """Exception for database operation errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)

async def faq_exception_handler(request: Request, exc: FAQProcessingError):
    """
    Handle custom FAQ processing exceptions.
    """
    logger.error(f"FAQ Processing Error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message}
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions.
    """
    logger.error(f"HTTP Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors.
    """
    error_details = []
    for error in exc.errors():
        error_details.append({
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"]
        })
    
    logger.error(f"Validation Error: {error_details}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "details": error_details
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handle unhandled exceptions.
    """
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "An unexpected error occurred. Please try again later."}
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI app.
    """
    app.add_exception_handler(FAQProcessingError, faq_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)