#!/usr/bin/env python3
"""
Keep-alive script to prevent Render free tier from sleeping
"""
import requests
import time
import os
from datetime import datetime

def ping_backend():
    """Ping the backend to keep it alive"""
    try:
        url = "https://prepandhirebackend.onrender.com/health"
        response = requests.get(url, timeout=10)
        print(f"[{datetime.now()}] Backend ping: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"[{datetime.now()}] Backend ping failed: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Starting keep-alive script for Render backend...")
    print("⏰ Pinging every 10 minutes to prevent sleep")
    
    while True:
        ping_backend()
        time.sleep(600)  # 10 minutes

