#!/bin/bash
# Complete AI Support Platform Startup Script
# Starts all services with one command

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║        AI Support Platform - Complete Deployment          ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo

# Change to deployment directory
cd "$(dirname "$0")"

# Check for .env file
if [ ! -f "../.env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found!${NC}"
    echo
    echo "Creating .env from template..."
    cp ../.env.example ../.env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo
    echo -e "${YELLOW}IMPORTANT: Edit .env and set your configuration!${NC}"
    echo "At minimum, set:"
    echo "  • OPENAI_API_KEY (if using OpenAI)"
    echo "  • MONGO_ROOT_PASSWORD"
    echo "  • REDIS_PASSWORD"
    echo "  • GRAFANA_ADMIN_PASSWORD"
    echo
    read -p "Press Enter after editing .env to continue..."
fi

# Load environment
source ../.env 2>/dev/null || true

echo
echo "═══════════════════════════════════════════════════════════"
echo " Configuration Summary"
echo "═══════════════════════════════════════════════════════════"
echo
echo "  Deployment Mode: ${DEPLOYMENT_MODE:-development}"
echo "  OpenAI Enabled: $([ -n "$OPENAI_API_KEY" ] && echo "✓ Yes" || echo "✗ No")"
echo "  A/B Testing: ${AB_TEST_ENABLED:-false}"
echo "  Training: ${ENABLE_TRAINING:-false}"
echo "  Domain: ${DOMAIN:-localhost}"
echo

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found!${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not found!${NC}"
    echo "Please install Docker Compose first"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed${NC}"
echo

# Detect NVIDIA GPU for training
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ NVIDIA GPU detected${NC}"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    GPU_AVAILABLE=true
else
    echo -e "${YELLOW}⚠️  No NVIDIA GPU detected${NC}"
    echo "  Training will be disabled or very slow"
    GPU_AVAILABLE=false
fi

echo
echo "═══════════════════════════════════════════════════════════"
echo " Deployment Options"
echo "═══════════════════════════════════════════════════════════"
echo
echo "  1) Full deployment (all features + training)"
echo "  2) Production (no training)"
echo "  3) Development (minimal)"
echo "  4) Training only"
echo "  5) Exit"
echo

read -p "Select option [1-5]: " OPTION

case $OPTION in
    1)
        echo
        echo -e "${BLUE}Starting FULL deployment...${NC}"
        echo

        # Pull images first
        echo "Pulling Docker images..."
        docker-compose -f docker-compose.full.yml pull || true

        # Build services
        echo "Building services..."
        docker-compose -f docker-compose.full.yml build

        # Start all services
        echo "Starting services..."
        docker-compose -f docker-compose.full.yml up -d

        # If training enabled and GPU available, start training
        if [ "${ENABLE_TRAINING}" = "true" ] && [ "$GPU_AVAILABLE" = true ]; then
            echo
            echo "Starting training service..."
            docker-compose -f docker-compose.full.yml --profile training up -d training-service

            echo
            echo "Follow training logs:"
            echo "  docker-compose -f docker-compose.full.yml logs -f training-service"
        fi
        ;;

    2)
        echo
        echo -e "${BLUE}Starting PRODUCTION deployment...${NC}"
        echo
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
        ;;

    3)
        echo
        echo -e "${BLUE}Starting DEVELOPMENT deployment...${NC}"
        echo
        docker-compose -f docker-compose.yml build
        docker-compose -f docker-compose.yml up -d
        ;;

    4)
        echo
        echo -e "${BLUE}Starting TRAINING ONLY...${NC}"
        echo

        if [ "$GPU_AVAILABLE" = false ]; then
            echo -e "${YELLOW}⚠️  No GPU detected - training will be VERY slow${NC}"
            read -p "Continue? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 0
            fi
        fi

        docker-compose -f docker-compose.full.yml --profile training up training-service
        exit 0
        ;;

    5)
        echo "Exiting..."
        exit 0
        ;;

    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

echo
echo "═══════════════════════════════════════════════════════════"
echo " Waiting for services to start..."
echo "═══════════════════════════════════════════════════════════"
echo

# Wait for backend to be healthy
echo -n "Waiting for backend..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

echo
echo "═══════════════════════════════════════════════════════════"
echo " 🎉 Deployment Complete!"
echo "═══════════════════════════════════════════════════════════"
echo
echo "Services are running at:"
echo
echo -e "  ${GREEN}Frontend:${NC}     http://localhost:3000"
echo -e "  ${GREEN}Backend API:${NC}  http://localhost:8000"
echo -e "  ${GREEN}API Docs:${NC}     http://localhost:8000/docs"
echo -e "  ${GREEN}LLM Service:${NC}  http://localhost:8001"
echo -e "  ${GREEN}RAG Service:${NC}  http://localhost:8002"
echo -e "  ${GREEN}Prometheus:${NC}   http://localhost:9090"
echo -e "  ${GREEN}Grafana:${NC}      http://localhost:3001"
echo
echo "Credentials:"
echo "  • Grafana: ${GRAFANA_ADMIN_USER:-admin} / ${GRAFANA_ADMIN_PASSWORD}"
echo "  • MongoDB: ${MONGO_ROOT_USER} / ${MONGO_ROOT_PASSWORD}"
echo
echo "Useful commands:"
echo "  • View logs:        docker-compose -f docker-compose.full.yml logs -f"
echo "  • Stop services:    docker-compose -f docker-compose.full.yml down"
echo "  • Restart:          docker-compose -f docker-compose.full.yml restart"
echo "  • Check status:     docker-compose -f docker-compose.full.yml ps"
echo

if [ "${ENABLE_TRAINING}" = "true" ]; then
    echo "Training status:"
    echo "  • Check logs:       docker-compose -f docker-compose.full.yml logs -f training-service"
    echo "  • Model location:   docker volume inspect deployment_training-models"
    echo
fi

echo "═══════════════════════════════════════════════════════════"
echo

# Open browser (optional)
if command -v xdg-open &> /dev/null; then
    read -p "Open frontend in browser? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        xdg-open http://localhost:3000
    fi
elif command -v open &> /dev/null; then
    read -p "Open frontend in browser? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open http://localhost:3000
    fi
fi

echo
echo "Enjoy your AI Support Platform! 🚀"
echo
