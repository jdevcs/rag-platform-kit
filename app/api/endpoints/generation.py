from fastapi import APIRouter, HTTPException, status
import time

from app.models.schemas import GenerationRequest, GenerationResponse, ErrorResponse, SearchQuery
from app.core.config import settings
from app.services.retrieval_service import retrieval_service
from app.services.llm_service import llm_service
from app.core.metrics import track_llm_generation
from loguru import logger

router = APIRouter()

@router.post(
    "/generate",
    response_model=GenerationResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
@track_llm_generation(settings.LLM_PROVIDER, settings.OLLAMA_MODEL if settings.LLM_PROVIDER == "ollama" else getattr(settings, f"{settings.LLM_PROVIDER.upper()}_MODEL", "unknown"))
async def generate_answer(request: GenerationRequest):
    """
    Generate an answer to a query using retrieved context.
    
    This endpoint can either use provided context or perform a retrieval
    step first if no context is provided.
    """
    start_time = time.time()
    
    try:
        # Retrieve context if not provided
        if not request.context:
            # Use provided search params or default to settings
            search_params = request.search_params or SearchQuery(
                query=request.query,
                top_k=settings.TOP_K,
                similarity_threshold=settings.SIMILARITY_THRESHOLD,
                filters=None
            )
            # Ensure query is set if caller provided search_params without query
            if not getattr(search_params, "query", None):
                search_params.query = request.query
            request.context = retrieval_service.retrieve(search_params)
        
        # Generate response
        answer = llm_service.generate_response(
            query=request.query,
            context=request.context or [],
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        generation_time = time.time() - start_time
        
        logger.info(f"Generated answer for query in {generation_time:.2f}s")
        
        return GenerationResponse(
            answer=answer,
            sources=request.context or [],
            generation_time=generation_time
        )
    
    except Exception as e:
        logger.error(f"Error in generation endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating answer: {str(e)}"
        )