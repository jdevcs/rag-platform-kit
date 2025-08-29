from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from loguru import logger
import asyncio

from app.core.config import settings
from app.api.endpoints import ingestion, retrieval, generation
from app.core.metrics import metrics_collector
from app.services.health_monitor import health_monitor

# Display startup information
print("🚀 Starting RAG Platform Kit...")
print(f"📍 Service will run on: {settings.SERVICE_HOST}:{settings.SERVICE_PORT}")
print(f"🔧 Vector Store: {settings.VECTOR_STORE_TYPE}")
print(f"🤖 LLM Provider: {settings.LLM_PROVIDER}")
print()

# Check if essential services are available
if settings.VECTOR_STORE_TYPE == "qdrant":
    try:
        import requests
        response = requests.get(f"{settings.QDRANT_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Qdrant vector store is accessible")
        else:
            print("⚠️  Qdrant vector store may not be running")
    except Exception as e:
        print("❌ Cannot connect to Qdrant vector store")
        print("   Make sure Qdrant is running on:", settings.QDRANT_URL)

print("="*50)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingestion.router, prefix=settings.API_V1_STR, tags=["ingestion"])
app.include_router(retrieval.router, prefix=settings.API_V1_STR, tags=["retrieval"])
app.include_router(generation.router, prefix=settings.API_V1_STR, tags=["generation"])

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Add custom metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get Prometheus metrics"""
    return metrics_collector.get_metrics()

@app.get("/")
async def root():
    return {"message": "RAG Microservice API", "version": settings.VERSION}

@app.get("/health")
async def health_check():
    """Enhanced health check with component status"""
    try:
        # Get comprehensive health summary
        health_summary = await health_monitor.get_health_summary()
        
        # Basic health status
        overall_status = "healthy"
        if (health_summary.get("vector_store", {}).get("status") == "unhealthy" or
            health_summary.get("llm_service", {}).get("status") == "unhealthy" or
            health_summary.get("system", {}).get("status") == "unhealthy"):
            overall_status = "degraded"
        
        health_status = {
            "status": overall_status,
            "vector_store": {
                "type": settings.VECTOR_STORE_TYPE,
                "status": health_summary.get("vector_store", {}).get("status", "unknown"),
                "embedding_model": settings.EMBEDDING_MODEL
            },
            "llm_service": {
                "provider": settings.LLM_PROVIDER,
                "model": health_summary.get("llm_service", {}).get("model", "unknown"),
                "status": health_summary.get("llm_service", {}).get("status", "unknown")
            },
            "system": health_summary.get("system", {}),
            "timestamp": health_summary.get("timestamp")
        }
        
        # Add provider-specific info
        if settings.LLM_PROVIDER == "ollama":
            health_status["llm_service"]["ollama_url"] = settings.OLLAMA_BASE_URL
        
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

@app.on_event("startup")
async def startup_event():
    """Start health monitoring on startup"""
    await health_monitor.start_monitoring()
    logger.info("Health monitoring started")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop health monitoring on shutdown"""
    await health_monitor.stop_monitoring()
    logger.info("Health monitoring stopped")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.RELOAD,
        workers=settings.WORKER_PROCESSES
    )