#!/bin/bash

# E-commerce Support AI - Quick Start Script
# Uruchamia backend i frontend dla szybkiego demo

set -e  # Exit on error

echo "🚀 E-commerce Support AI - Quick Start"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10+"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# 1. Install Backend dependencies
echo "📦 Installing Backend dependencies..."
cd backend
if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt
cd ..
echo "✅ Backend dependencies installed"
echo ""

# 2. Install RAG dependencies
echo "📦 Installing RAG dependencies..."
cd rag
pip install -q -r requirements.txt

# Build FAISS index if not exists
if [ ! -f "vectorstore/faiss.index" ]; then
    echo "   Building FAISS index (first time only)..."
    python retriever.py > /dev/null 2>&1 || echo "   ⚠️  FAISS index build skipped (will use mock data)"
fi
cd ..
echo "✅ RAG system ready"
echo ""

# 3. Install Frontend dependencies
echo "📦 Installing Frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install --silent
fi
cd ..
echo "✅ Frontend dependencies installed"
echo ""

# 4. Start Backend (in background)
echo "🚀 Starting Backend API on http://localhost:8000..."
cd backend
source venv/bin/activate
nohup python app/main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
cd ..

# Wait for backend to start
echo "   Waiting for backend to be ready..."
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running!"
else
    echo "⚠️  Backend may not be fully ready yet (check logs/backend.log)"
fi
echo ""

# 5. Start Frontend
echo "🚀 Starting Frontend on http://localhost:3000..."
cd frontend

# Create .env.local if not exists
if [ ! -f ".env.local" ]; then
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
fi

npm run dev &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"
cd ..

echo ""
echo "============================================"
echo "✅ E-commerce Support AI is running!"
echo "============================================"
echo ""
echo "📍 Services:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📊 Try these queries:"
echo "   - 'Jak mogę zwrócić produkt?'"
echo "   - 'Jakie są koszty dostawy?'"
echo "   - 'Chcę zmienić adres dostawy'"
echo ""
echo "🛑 To stop services:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "📝 Logs:"
echo "   Backend:  logs/backend.log"
echo "   Frontend: Check terminal output"
echo ""
echo "Happy testing! 🎉"
