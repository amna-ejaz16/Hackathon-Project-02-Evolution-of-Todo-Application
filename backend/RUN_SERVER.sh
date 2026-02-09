#!/bin/bash
# FastAPI Backend Server Launcher
# AI-Powered Todo Application - Phase 3 AI Chatbot

echo "================================"
echo "Backend Server Startup Guide"
echo "================================"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found"
    echo "Creating new virtual environment..."
    python -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Verify dependencies
echo ""
echo "Verifying openai-agents installation..."
python -c "from agents import Agent, Runner; print('✅ agents module available')" 2>&1 || {
    echo "⚠️  agents module missing, reinstalling dependencies..."
    pip install -r requirements.txt
}

# Verify app imports
echo ""
echo "Verifying app imports..."
python -c "from src.main import app; print('✅ App loads successfully')" 2>&1 || {
    echo "❌ App import failed"
    exit 1
}

# Start server
echo ""
echo "================================"
echo "Starting FastAPI Server..."
echo "================================"
echo ""
echo "Server will run on: http://localhost:8000"
echo "API Docs:          http://localhost:8000/docs"
echo "ReDoc:             http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
