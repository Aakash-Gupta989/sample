#!/bin/bash

echo "🚀 Starting EduAI - Visual Learning Assistant"
echo "============================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please run setup.sh first"
    exit 1
fi

# Check if OPENAI_API_KEY is set
if ! grep -q "OPENAI_API_KEY=sk_" .env 2>/dev/null; then
    echo "⚠️  Warning: OPENAI_API_KEY not set in .env file"
    echo "   Please add your OpenAI API key to the .env file"
fi

# Function to start backend
start_backend() {
    echo "🔧 Starting backend server..."
    cd backend
    python main.py &
    BACKEND_PID=$!
    cd ..
    echo "✅ Backend started (PID: $BACKEND_PID)"
}

# Function to start frontend
start_frontend() {
    echo "🎨 Starting frontend server..."
    cd frontend
    npm start &
    FRONTEND_PID=$!
    cd ..
    echo "✅ Frontend started (PID: $FRONTEND_PID)"
}

# Start both services
start_backend
sleep 2
start_frontend

echo ""
echo "🎉 EduAI is starting up!"
echo ""
echo "📍 Access points:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo ""
echo "⏹️  To stop all services, press Ctrl+C"
echo ""

# Wait for interrupt
trap 'echo "🛑 Shutting down..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit' INT

# Keep script running
wait
