# 🚀 EduAI Setup Instructions

## 📍 Current Status
✅ **Complete system built and ready to run!**

## 🔑 IMPORTANT: Add Your OpenAI API Key

Provide your OpenAI API key in `.env`:

```bash
# In .env file:
OPENAI_API_KEY=sk_...
OPENAI_MODEL=gpt-4o
```

## 🚀 Quick Start (3 Steps)

### Step 1: Setup (One-time)
```bash
./setup.sh
```

### Step 2: Add API Key
Edit `.env` file and add your OpenAI API key

### Step 3: Start Application
```bash
./start.sh
```

## 🌐 Access Your Application
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000

## 🧪 Test with Heat Transfer

1. **Draw**: Simple heat transfer diagram (metal rod + flame)
2. **Speak**: Click 🎤 and say "This shows heat conduction through a metal rod"
3. **Watch**: AI analyzes and asks follow-up questions!

## 📁 Where Everything Is

```
/Users/aakashgupta/Desktop/New Project/
├── .env                 ← ADD YOUR API KEY HERE
├── setup.sh            ← Run this first
├── start.sh            ← Run this to start
├── README.md           ← Full documentation
├── backend/            ← Python FastAPI server
└── frontend/           ← React application
```

## 🔧 Manual Start (Alternative)

If scripts don't work:

**Terminal 1 (Backend):**
```bash
cd backend
python main.py
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm start
```

## ❓ Need Help?

1. **Check README.md** for detailed instructions
2. **Troubleshooting section** has common solutions
3. **Health check**: Visit http://localhost:8000/health

## 🎯 What You Built

- **Real-time whiteboard** with drawing tools
- **Voice input** with speech-to-text
- **Multimodal analysis** using GPT-4o
- **Dynamic interview questions** - no hardcoded questions!

**Ready to test your heat transfer scenario! 🔥**
