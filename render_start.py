#!/usr/bin/env python3
"""
Render.com deployment start script for Genshin Impact Personal Assistant API
"""

import os
import sys
import uvicorn
from config import settings

def main():
    """Start the FastAPI application with Render.com optimized settings."""
    
    # Get port from environment (Render sets this automatically)
    port = int(os.environ.get("PORT", 8000))
    
    # Set host to 0.0.0.0 for Render
    host = "0.0.0.0"
    
    # Production settings for Render
    uvicorn_config = {
        "app": "main:app",
        "host": host,
        "port": port,
        "workers": 1,  # Single worker for free tier
        "log_level": "info",
        "access_log": True,
        "use_colors": False,  # Better for production logs
        "loop": "asyncio",
        "http": "httptools",
    }
    
    print(f"🚀 Starting Genshin Impact API on {host}:{port}")
    print(f"📊 Environment: {settings.environment}")
    print(f"🗄️  Database: {'Connected' if settings.mongodb_url else 'Not configured'}")
    
    # Start the server
    uvicorn.run(**uvicorn_config)

if __name__ == "__main__":
    main() 