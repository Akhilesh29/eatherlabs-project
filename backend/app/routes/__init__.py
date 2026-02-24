from .documents import router as documents_router
from .compare import router as compare_router
from .report import router as report_router

__all__ = ["documents_router", "compare_router", "report_router"]
