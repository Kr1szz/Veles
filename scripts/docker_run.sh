#!/usr/bin/env bash
set -e

echo "=================================================================="
echo "Veles Shield — Docker & Container Infrastructure Deployment Script"
echo "=================================================================="

# Check Docker CLI
if ! command -v docker &> /dev/null; then
    echo "ERROR: 'docker' is not installed. Please install Docker Engine."
    exit 1
fi

# Test Docker daemon socket permissions
DOCKER_CMD="docker"
if ! docker ps &> /dev/null; then
    echo "Notice: Non-root user cannot access /var/run/docker.sock directly."
    if command -v sudo &> /dev/null; then
        echo "Attempting execution with sudo..."
        DOCKER_CMD="sudo docker"
    else
        echo "Tip: Run 'sudo usermod -aG docker \$USER && newgrp docker' to enable non-root Docker."
        exit 1
    fi
fi

echo "Deploying Veles Shield microservices via Docker Compose..."
echo "- Veles API Gateway (FastAPI + C++20 SIMD Engine)"
echo "- Veles Frontend (React 19 + Nginx Alpine)"
echo "- PostgreSQL 16 (Auditable Ledger & DPDPA)"
echo "- Redis 7 Alpine (Sliding Window Velocity Counter)"
echo "------------------------------------------------------------------"

$DOCKER_CMD compose up --build -d

echo ""
echo "Deployment successful! Checking service status..."
$DOCKER_CMD compose ps

echo ""
echo "=================================================================="
echo "Veles Shield Services Operational:"
echo "- Dashboard UI:         http://localhost:3000"
echo "- API Gateway / Docs:   http://localhost:8000/docs"
echo "- Health Check:         http://localhost:8000/health"
echo "=================================================================="
