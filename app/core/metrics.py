"""
Comprehensive metrics collection for RAG Platform Kit.
Implements industry-standard metrics for RAG systems including:
- Application performance metrics
- RAG-specific operation metrics
- Infrastructure health metrics
- Business metrics
"""

from prometheus_client import (
    Counter, Histogram, Gauge, Summary, Info,
    generate_latest, CONTENT_TYPE_LATEST
)
from prometheus_client.core import REGISTRY
import time
from typing import Dict, Any, Optional
from functools import wraps
import psutil
import os
from loguru import logger

# Application Performance Metrics
REQUEST_COUNT = Counter(
    'rag_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'rag_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

REQUEST_LATENCY = Histogram(
    'rag_request_latency_seconds',
    'Request latency in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

ERROR_COUNT = Counter(
    'rag_errors_total',
    'Total number of errors',
    ['method', 'endpoint', 'error_type']
)

# RAG-Specific Metrics
DOCUMENT_PROCESSING_DURATION = Histogram(
    'rag_document_processing_duration_seconds',
    'Document processing duration in seconds',
    ['file_type', 'status'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

CHUNKS_CREATED = Counter(
    'rag_chunks_created_total',
    'Total number of chunks created',
    ['file_type', 'status']
)

EMBEDDING_GENERATION_DURATION = Histogram(
    'rag_embedding_generation_duration_seconds',
    'Embedding generation duration in seconds',
    ['model', 'batch_size'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

VECTOR_SEARCH_DURATION = Histogram(
    'rag_vector_search_duration_seconds',
    'Vector search duration in seconds',
    ['vector_store', 'top_k'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
)

VECTOR_SEARCH_ACCURACY = Histogram(
    'rag_vector_search_similarity_scores',
    'Vector search similarity scores',
    ['vector_store', 'top_k'],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

LLM_GENERATION_DURATION = Histogram(
    'rag_llm_generation_duration_seconds',
    'LLM response generation duration in seconds',
    ['provider', 'model', 'status'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

LLM_TOKENS_USED = Counter(
    'rag_llm_tokens_total',
    'Total tokens used by LLM',
    ['provider', 'model', 'token_type']
)

# Infrastructure Health Metrics
SYSTEM_MEMORY_USAGE = Gauge(
    'rag_system_memory_bytes',
    'System memory usage in bytes',
    ['type']
)

SYSTEM_CPU_USAGE = Gauge(
    'rag_system_cpu_percent',
    'System CPU usage percentage'
)

VECTOR_STORE_HEALTH = Gauge(
    'rag_vector_store_health',
    'Vector store health status (1=healthy, 0=unhealthy)',
    ['vector_store_type']
)

LLM_SERVICE_HEALTH = Gauge(
    'rag_llm_service_health',
    'LLM service health status (1=healthy, 0=unhealthy)',
    ['provider', 'model']
)

# Business Metrics
DOCUMENTS_PROCESSED_TODAY = Counter(
    'rag_documents_processed_total',
    'Total documents processed',
    ['file_type', 'status']
)

SEARCH_QUERIES_TODAY = Counter(
    'rag_search_queries_total',
    'Total search queries processed',
    ['query_type', 'status']
)

GENERATION_REQUESTS_TODAY = Counter(
    'rag_generation_requests_total',
    'Total generation requests processed',
    ['status']
)

# System Information
SYSTEM_INFO = Info('rag_system', 'RAG Platform system information')

class MetricsCollector:
    """Centralized metrics collection for RAG operations"""
    
    def __init__(self):
        self.start_time = time.time()
        self._set_system_info()
    
    def _set_system_info(self):
        """Set system information metrics"""
        try:
            SYSTEM_INFO.info({
                'version': '1.0.0',
                'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                'platform': os.sys.platform,
                'architecture': os.arch[0] if hasattr(os, 'arch') else 'unknown'
            })
        except Exception as e:
            logger.warning(f"Could not set system info: {e}")
    
    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics"""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_error(self, method: str, endpoint: str, error_type: str):
        """Record error metrics"""
        ERROR_COUNT.labels(method=method, endpoint=endpoint, error_type=error_type).inc()
    
    def record_document_processing(self, file_type: str, status: str, duration: float, chunks: int):
        """Record document processing metrics"""
        DOCUMENT_PROCESSING_DURATION.labels(file_type=file_type, status=status).observe(duration)
        CHUNKS_CREATED.labels(file_type=file_type, status=status).inc(chunks)
        DOCUMENTS_PROCESSED_TODAY.labels(file_type=file_type, status=status).inc()
    
    def record_embedding_generation(self, model: str, batch_size: int, duration: float):
        """Record embedding generation metrics"""
        EMBEDDING_GENERATION_DURATION.labels(model=model, batch_size=batch_size).observe(duration)
    
    def record_vector_search(self, vector_store: str, top_k: int, duration: float, similarity_scores: list):
        """Record vector search metrics"""
        VECTOR_SEARCH_DURATION.labels(vector_store=vector_store, top_k=top_k).observe(duration)
        for score in similarity_scores:
            VECTOR_SEARCH_ACCURACY.labels(vector_store=vector_store, top_k=top_k).observe(score)
        SEARCH_QUERIES_TODAY.labels(query_type='vector_search', status='success').inc()
    
    def record_llm_generation(self, provider: str, model: str, status: str, duration: float, 
                             input_tokens: int = 0, output_tokens: int = 0):
        """Record LLM generation metrics"""
        LLM_GENERATION_DURATION.labels(provider=provider, model=model, status=status).observe(duration)
        if input_tokens > 0:
            LLM_TOKENS_USED.labels(provider=provider, model=model, token_type='input').inc(input_tokens)
        if output_tokens > 0:
            LLM_TOKENS_USED.labels(provider=provider, model=model, token_type='output').inc(output_tokens)
        GENERATION_REQUESTS_TODAY.labels(status=status).inc()
    
    def record_vector_store_health(self, vector_store_type: str, is_healthy: bool):
        """Record vector store health status"""
        VECTOR_STORE_HEALTH.labels(vector_store_type=vector_store_type).set(1 if is_healthy else 0)
    
    def record_llm_service_health(self, provider: str, model: str, is_healthy: bool):
        """Record LLM service health status"""
        LLM_SERVICE_HEALTH.labels(provider=provider, model=model).set(1 if is_healthy else 0)
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        try:
            # Memory metrics
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY_USAGE.labels(type='total').set(memory.total)
            SYSTEM_MEMORY_USAGE.labels(type='available').set(memory.available)
            SYSTEM_MEMORY_USAGE.labels(type='used').set(memory.used)
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_CPU_USAGE.set(cpu_percent)
        except Exception as e:
            logger.warning(f"Could not update system metrics: {e}")
    
    def get_metrics(self):
        """Get all metrics in Prometheus format"""
        return generate_latest(REGISTRY)

# Global metrics collector instance
metrics_collector = MetricsCollector()

def metrics_middleware(func):
    """Decorator to automatically collect metrics for endpoints"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        method = "POST"  # Most RAG endpoints are POST
        endpoint = func.__name__
        
        try:
            result = await func(*args, **kwargs)
            status = 200
            return result
        except Exception as e:
            status = 500
            error_type = type(e).__name__
            metrics_collector.record_error(method, endpoint, error_type)
            raise
        finally:
            duration = time.time() - start_time
            metrics_collector.record_request(method, endpoint, status, duration)
    
    return wrapper

def track_document_processing(file_type: str, status: str = 'success'):
    """Decorator to track document processing metrics"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                chunks = getattr(result, 'chunks_created', 0)
                metrics_collector.record_document_processing(file_type, status, duration, chunks)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics_collector.record_document_processing(file_type, 'error', duration, 0)
                raise
        return wrapper
    return decorator

def track_vector_search(vector_store: str, top_k: int):
    """Decorator to track vector search metrics"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                similarity_scores = [getattr(r, 'similarity_score', 0.0) for r in result]
                metrics_collector.record_vector_search(vector_store, top_k, duration, similarity_scores)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics_collector.record_vector_search(vector_store, top_k, duration, [])
                raise
        return wrapper
    return decorator

def track_llm_generation(provider: str, model: str):
    """Decorator to track LLM generation metrics"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                metrics_collector.record_llm_generation(provider, model, 'success', duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics_collector.record_llm_generation(provider, model, 'error', duration)
                raise
        return wrapper
    return decorator
