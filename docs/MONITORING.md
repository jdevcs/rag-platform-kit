# RAG Platform Kit - Monitoring & Observability Guide

## Overview

The RAG Platform Kit includes a comprehensive monitoring and observability system built on industry-standard tools and practices. This system provides real-time visibility into the health, performance, and operational metrics of your RAG platform.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RAG Service  │    │   Prometheus    │    │     Grafana     │
│                 │    │                 │    │                 │
│ • Custom       │───▶│ • Metrics       │───▶│ • Dashboards    │
│   Metrics      │    │   Collection    │    │ • Visualization │
│ • Health       │    │ • Alerting      │    │ • Alerts        │
│   Checks       │    │ • Storage       │    │ • Reporting     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Metrics Collection

### 1. Application Performance Metrics

#### Request Metrics
- **`rag_requests_total`**: Total number of HTTP requests by method, endpoint, and status
- **`rag_request_duration_seconds`**: Request duration distribution with configurable buckets
- **`rag_request_latency_seconds`**: Request latency for performance analysis
- **`rag_errors_total`**: Error count by type, method, and endpoint

**Use Cases:**
- Monitor API performance and identify slow endpoints
- Track error rates and types for debugging
- Set SLOs for response time and availability

#### Example Queries:
```promql
# Request rate by endpoint
rate(rag_requests_total[5m])

# 95th percentile response time
histogram_quantile(0.95, rate(rag_request_duration_seconds_bucket[5m]))

# Error rate by type
rate(rag_errors_total[5m])
```

### 2. RAG-Specific Metrics

#### Document Processing Metrics
- **`rag_document_processing_duration_seconds`**: Time to process documents by file type and status
- **`rag_chunks_created_total`**: Number of chunks created during processing
- **`rag_embedding_generation_duration_seconds`**: Time to generate embeddings by model and batch size

**Use Cases:**
- Monitor document processing pipeline performance
- Identify bottlenecks in chunking and embedding generation
- Track processing success/failure rates

#### Vector Search Metrics
- **`rag_vector_search_duration_seconds`**: Vector search performance by store type and top_k
- **`rag_vector_search_similarity_scores`**: Distribution of similarity scores for quality analysis

**Use Cases:**
- Monitor search performance and latency
- Analyze search result quality
- Optimize vector store configuration

#### LLM Generation Metrics
- **`rag_llm_generation_duration_seconds`**: Response generation time by provider and model
- **`rag_llm_tokens_total`**: Token usage by provider, model, and type (input/output)

**Use Cases:**
- Monitor LLM performance and costs
- Track token usage patterns
- Identify slow or failing LLM providers

### 3. Infrastructure Health Metrics

#### System Resource Metrics
- **`rag_system_memory_bytes`**: Memory usage by type (total, used, available)
- **`rag_system_cpu_percent`**: CPU usage percentage

**Use Cases:**
- Monitor system resource utilization
- Set capacity planning thresholds
- Identify resource bottlenecks

#### Service Health Metrics
- **`rag_vector_store_health`**: Health status of vector stores (1=healthy, 0=unhealthy)
- **`rag_llm_service_health`**: Health status of LLM services

**Use Cases:**
- Monitor service availability
- Set up automated alerting
- Track service reliability

### 4. Business Metrics

#### Operational Metrics
- **`rag_documents_processed_total`**: Daily document processing volume
- **`rag_search_queries_total`**: Search query volume and success rates
- **`rag_generation_requests_total`**: Generation request volume and success rates

**Use Cases:**
- Track platform usage and adoption
- Monitor business KPIs
- Capacity planning and scaling decisions

## Alerting Rules

### Critical Alerts

#### High Error Rate
- **Trigger**: Error rate > 0.1 errors/second over 5 minutes
- **Severity**: Critical
- **Action**: Immediate investigation required

#### Service Unavailable
- **Trigger**: Service down for > 1 minute
- **Severity**: Critical
- **Action**: Service restart and investigation

#### Vector Store Unhealthy
- **Trigger**: Vector store health check fails
- **Severity**: Critical
- **Action**: Check vector store connectivity and configuration

### Warning Alerts

#### High Response Time
- **Trigger**: 95th percentile response time > 5 seconds
- **Severity**: Warning
- **Action**: Performance investigation and optimization

#### High Resource Usage
- **Trigger**: Memory usage > 90% or CPU > 80%
- **Severity**: Warning
- **Action**: Resource monitoring and potential scaling

### Informational Alerts

#### High Volume
- **Trigger**: Unusually high request volumes
- **Severity**: Info
- **Action**: Monitor for potential issues or scaling needs

## Dashboard Configuration

### RAG Platform Overview Dashboard

The main dashboard provides a comprehensive view of all platform metrics:

1. **System Health Status**: Real-time health indicators for all components
2. **Request Rate**: API usage patterns and trends
3. **Response Time**: Performance metrics with percentile breakdowns
4. **Error Rate**: Error tracking and analysis
5. **Document Processing**: Pipeline performance and throughput
6. **Vector Search**: Search performance and quality metrics
7. **LLM Generation**: Generation performance and token usage
8. **System Resources**: CPU and memory utilization
9. **Business Metrics**: Operational KPIs and trends

### Dashboard Access

- **URL**: http://localhost:3000
- **Default Credentials**: admin/admin
- **Dashboard Path**: RAG Platform → RAG Platform Overview

## Monitoring Setup

### 1. Start the Monitoring Stack

```bash
# Start all services including monitoring
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 2. Access Monitoring Tools

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **RAG Service Metrics**: http://localhost:8000/metrics

### 3. Verify Metrics Collection

```bash
# Check if metrics endpoint is working
curl http://localhost:8000/metrics

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets
```

## Troubleshooting

### Common Issues

#### Metrics Not Appearing
1. Check if the RAG service is running: `docker-compose ps`
2. Verify metrics endpoint: `curl http://localhost:8000/metrics`
3. Check Prometheus targets: http://localhost:9090/targets
4. Verify network connectivity between services

#### High Error Rates
1. Check application logs: `docker-compose logs rag-service`
2. Review error metrics in Grafana
3. Check dependent services (vector store, LLM)
4. Verify configuration and API keys

#### Performance Issues
1. Monitor response time metrics
2. Check system resource usage
3. Review vector search performance
4. Analyze LLM generation times

### Debugging Commands

```bash
# Check service health
curl http://localhost:8000/health

# View service logs
docker-compose logs -f rag-service

# Check Prometheus configuration
docker-compose exec prometheus cat /etc/prometheus/prometheus.yml

# Restart monitoring services
docker-compose restart prometheus grafana
```

## Best Practices

### 1. Metric Naming
- Use descriptive names that clearly indicate what is being measured
- Include relevant labels for filtering and grouping
- Follow Prometheus naming conventions

### 2. Alerting
- Set appropriate thresholds based on your SLOs
- Use different severity levels for different types of issues
- Include actionable information in alert descriptions

### 3. Dashboard Design
- Group related metrics logically
- Use appropriate visualization types for different metrics
- Include time ranges that make sense for your use case

### 4. Performance Monitoring
- Monitor both application and infrastructure metrics
- Set up baselines for normal operation
- Track trends over time to identify patterns

## Scaling Considerations

### High-Volume Deployments
- Increase Prometheus storage retention for longer historical data
- Use Prometheus federation for multiple instances
- Consider using Thanos or Cortex for long-term storage

### Multi-Environment Monitoring
- Use different Prometheus instances for different environments
- Implement metric filtering and aggregation
- Set up cross-environment dashboards

## Security

### Access Control
- Restrict Prometheus and Grafana access to authorized users
- Use reverse proxy with authentication if needed
- Monitor access logs for suspicious activity

### Data Privacy
- Ensure sensitive data is not exposed in metrics
- Use appropriate labeling to avoid PII exposure
- Regular audit of metric collection

## Integration

### External Monitoring Systems
- Prometheus can be integrated with various alert managers
- Grafana supports multiple data sources
- Metrics can be exported to external systems via remote write

### CI/CD Integration
- Include monitoring configuration in deployment pipelines
- Validate metrics collection after deployments
- Use monitoring data for deployment success criteria

## Support and Maintenance

### Regular Tasks
- Monitor alert effectiveness and adjust thresholds
- Review and update dashboard configurations
- Clean up old metrics and alerts
- Update monitoring stack versions

### Documentation Updates
- Keep this guide updated with configuration changes
- Document custom metrics and their purpose
- Maintain runbook links in alert configurations

---

For additional support or questions about the monitoring system, please refer to the project documentation or create an issue in the project repository.
