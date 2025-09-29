#!/bin/bash

echo "🚀 Setting up EduAI - Visual Learning Assistant"
echo "================================================"

echo "✅ Pre-flight checks"

# Set up backend
echo "🔧 Setting up backend..."
cd backend

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

cd ..

# Set up frontend
echo "🔧 Setting up frontend..."
cd frontend

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 16+"
    exit 1
fi

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

cd ..

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp env.example .env
    echo "⚠️  Please edit .env file and add your OPENAI_API_KEY"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file and add your OPENAI_API_KEY"
echo "2. Start the backend: cd backend && python main.py"
echo "3. Start the frontend: cd frontend && npm start"
echo "4. Open http://localhost:3000 in your browser"
echo ""
echo "🔑 Use your OpenAI API key."
