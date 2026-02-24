"""Compare all parsed documents and return contradictions."""
from fastapi import APIRouter

from app.routes.documents import get_parsed_documents
from app.services.comparison import compare_documents

router = APIRouter(prefix="/api/compare", tags=["compare"])


@router.get("")
async def compare():
    """
    Run comparison on all currently parsed documents.
    Returns contradictions and summary.
    """
    documents = get_parsed_documents()
    if not documents:
        return {
            "total_documents": 0,
            "documents_consistent": 0,
            "contradictions": [],
            "summary": "No documents to compare. Upload and parse documents first.",
        }
    result = compare_documents(documents)
    return result.model_dump(mode="json")
