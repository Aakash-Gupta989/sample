#!/usr/bin/env python3
"""
Lightweight startup script for Render free tier
Optimized for memory constraints
"""

import os
import sys
import uvicorn
from main import app

def main():
    """Start the FastAPI application with Render-optimized settings"""
    
    # Get port from environment (Render sets this)
    port = int(os.getenv("PORT", 8000))
    
    # Render-optimized settings (without httptools for compatibility)
    config = {
        "host": "0.0.0.0",
        "port": port,
        "workers": 1,  # Single worker for free tier
        "log_level": "info",
        "access_log": True,
        "reload": False,  # Disable reload for production
        "loop": "asyncio",
        # Removed httptools for compatibility
    }
    
    print(f"🚀 Starting prepandhire-backend on port {port}")
    print(f"🔧 Memory-optimized configuration for Render free tier")
    
    try:
        uvicorn.run("main:app", **config)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
