#!/bin/bash

# RAG Platform Kit - Monitoring Quick Start Script
# This script starts the monitoring stack and verifies it's working

set -e

echo "🚀 Starting RAG Platform Monitoring Stack..."
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

print_status "Docker is running"

# Check if docker compose is available
if ! docker compose version &> /dev/null; then
    print_error "docker compose is not available. Please ensure Docker is installed and try again."
    exit 1
fi

print_status "docker compose is available"

# Start the monitoring stack
print_status "Starting monitoring services..."
docker compose up -d prometheus grafana

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Check if services are running
print_status "Checking service status..."
if docker compose ps prometheus grafana | grep -q "Up"; then
    print_success "Monitoring services are running"
else
    print_error "Some monitoring services failed to start"
    docker compose ps prometheus grafana
    exit 1
fi

# Wait a bit more for services to fully initialize
print_status "Waiting for services to fully initialize..."
sleep 20

# Check Prometheus targets
print_status "Checking Prometheus targets..."
if curl -s http://localhost:9090/api/v1/targets > /dev/null; then
    print_success "Prometheus is accessible"
else
    print_warning "Prometheus might not be fully ready yet"
fi

# Check Grafana
print_status "Checking Grafana..."
if curl -s http://localhost:3000 > /dev/null; then
    print_success "Grafana is accessible"
else
    print_warning "Grafana might not be fully ready yet"
fi

echo ""
echo "🎉 Monitoring Stack Started Successfully!"
echo "=============================================="
echo ""
echo "📊 Access URLs:"
echo "   • Prometheus: http://localhost:9090"
echo "   • Grafana:    http://localhost:3000 (admin/admin)"
echo ""
echo "🔍 Quick Checks:"
echo "   • Check Prometheus targets: http://localhost:9090/targets"
echo "   • View Grafana dashboards: http://localhost:3000/dashboards"
echo ""
echo "📝 Next Steps:"
echo "   1. Open Grafana in your browser"
echo "   2. Login with admin/admin"
echo "   3. Navigate to 'RAG Platform' folder"
echo "   4. Open 'RAG Platform Overview' dashboard"
echo ""
echo "🛠️  Useful Commands:"
echo "   • View logs: docker compose logs -f prometheus grafana"
echo "   • Stop services: docker compose stop prometheus grafana"
echo "   • Restart services: docker compose restart prometheus grafana"
echo "   • Check status: docker compose ps prometheus grafana"
echo ""

# Check if RAG service is also running
if docker compose ps rag-service | grep -q "Up"; then
    print_success "RAG service is also running - metrics will be collected automatically"
    echo "   • RAG Service Metrics: http://localhost:8000/metrics"
    echo "   • RAG Service Health: http://localhost:8000/health"
else
    print_warning "RAG service is not running - start it to collect metrics:"
    echo "   docker compose up -d rag-service"
fi

echo ""
echo "✅ Monitoring setup complete! Happy monitoring! 🎯"
