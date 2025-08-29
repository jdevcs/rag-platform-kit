"""
Health monitoring service for RAG Platform Kit.
Continuously monitors the health of various components and updates metrics.
"""

import asyncio
import time
from typing import Dict, Any
import requests
from loguru import logger

from app.core.config import settings
from app.core.metrics import metrics_collector
from app.core.vector_store import vector_store
from app.services.llm_service import llm_service

class HealthMonitor:
    """Monitors the health of various RAG platform components"""
    
    def __init__(self):
        self.monitoring_interval = 30  # seconds
        self.is_running = False
        self.monitoring_task = None
    
    async def start_monitoring(self):
        """Start the health monitoring loop"""
        if self.is_running:
            logger.warning("Health monitoring is already running")
            return
        
        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop the health monitoring loop"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                await self._check_all_components()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _check_all_components(self):
        """Check health of all components"""
        await asyncio.gather(
            self._check_vector_store_health(),
            self._check_llm_service_health(),
            self._update_system_metrics()
        )
    
    async def _check_vector_store_health(self):
        """Check vector store health"""
        try:
            if settings.VECTOR_STORE_TYPE == "chroma":
                # Check if ChromaDB collection is accessible
                collection_info = vector_store.collection.count()
                is_healthy = collection_info >= 0
                metrics_collector.record_vector_store_health("chroma", is_healthy)
                
            elif settings.VECTOR_STORE_TYPE == "qdrant":
                # Check Qdrant health endpoint
                try:
                    response = requests.get(f"{settings.QDRANT_URL}/health", timeout=5)
                    is_healthy = response.status_code == 200
                except Exception:
                    is_healthy = False
                metrics_collector.record_vector_store_health("qdrant", is_healthy)
                
            elif settings.VECTOR_STORE_TYPE == "redis":
                # Check Redis connection
                try:
                    vector_store.client.ping()
                    is_healthy = True
                except Exception:
                    is_healthy = False
                metrics_collector.record_vector_store_health("redis", is_healthy)
                
        except Exception as e:
            logger.error(f"Error checking vector store health: {e}")
            metrics_collector.record_vector_store_health(settings.VECTOR_STORE_TYPE, False)
    
    async def _check_llm_service_health(self):
        """Check LLM service health"""
        try:
            if settings.LLM_PROVIDER == "ollama":
                # Check Ollama health
                try:
                    response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
                    is_healthy = response.status_code == 200
                except Exception:
                    is_healthy = False
                metrics_collector.record_llm_service_health("ollama", settings.OLLAMA_MODEL, is_healthy)
                
            elif settings.LLM_PROVIDER == "openai":
                # Check OpenAI API key validity (basic check)
                is_healthy = bool(settings.OPENAI_API_KEY)
                metrics_collector.record_llm_service_health("openai", settings.OPENAI_MODEL, is_healthy)
                
            elif settings.LLM_PROVIDER == "cohere":
                # Check Cohere API key validity (basic check)
                is_healthy = bool(settings.COHERE_API_KEY)
                metrics_collector.record_llm_service_health("cohere", settings.COHERE_MODEL, is_healthy)
                
            elif settings.LLM_PROVIDER == "huggingface":
                # Check HuggingFace API key validity (basic check)
                is_healthy = bool(settings.HUGGINGFACE_API_KEY)
                metrics_collector.record_llm_service_health("huggingface", settings.HUGGINGFACE_MODEL, is_healthy)
                
        except Exception as e:
            logger.error(f"Error checking LLM service health: {e}")
            metrics_collector.record_llm_service_health(settings.LLM_PROVIDER, "unknown", False)
    
    async def _update_system_metrics(self):
        """Update system resource metrics"""
        try:
            metrics_collector.update_system_metrics()
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    async def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of all component health statuses"""
        try:
            summary = {
                "timestamp": time.time(),
                "vector_store": {
                    "type": settings.VECTOR_STORE_TYPE,
                    "status": "unknown"
                },
                "llm_service": {
                    "provider": settings.LLM_PROVIDER,
                    "model": getattr(settings, f"{settings.LLM_PROVIDER.upper()}_MODEL", "unknown"),
                    "status": "unknown"
                },
                "system": {
                    "status": "unknown"
                }
            }
            
            # Get vector store health
            if settings.VECTOR_STORE_TYPE == "chroma":
                try:
                    collection_info = vector_store.collection.count()
                    summary["vector_store"]["status"] = "healthy" if collection_info >= 0 else "unhealthy"
                except Exception:
                    summary["vector_store"]["status"] = "unhealthy"
            
            # Get LLM service health
            if settings.LLM_PROVIDER == "ollama":
                try:
                    response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
                    summary["llm_service"]["status"] = "healthy" if response.status_code == 200 else "unhealthy"
                except Exception:
                    summary["llm_service"]["status"] = "unhealthy"
            
            # Get system health (basic check)
            try:
                import psutil
                memory = psutil.virtual_memory()
                summary["system"]["status"] = "healthy" if memory.available > 0 else "unhealthy"
            except Exception:
                summary["system"]["status"] = "unknown"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting health summary: {e}")
            return {
                "timestamp": time.time(),
                "error": str(e)
            }

# Global health monitor instance
health_monitor = HealthMonitor()
