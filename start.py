#!/usr/bin/env python3
"""
Startup script for Genshin Impact Personal Assistant API
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def check_requirements():
    """Check if all required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        import genshin
        import motor
        import pymongo
        import langchain
        import langchain_google_genai
        import googleapiclient
        import python_dotenv
        import pydantic
        import pydantic_settings
        import httpx
        import apscheduler
        print("✅ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_environment():
    """Check if environment variables are properly configured."""
    required_vars = [
        "GOOGLE_API_KEY",
        "GOOGLE_CSE_ID", 
        "GOOGLE_CSE_API_KEY"
    ]
    
    # Load .env file if it exists
    env_file = Path(".env")
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded environment variables from .env file")
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please create a .env file with the required variables")
        print("See README.md for setup instructions")
        return False
    
    print("✅ All required environment variables are set")
    return True

def check_mongodb():
    """Check if MongoDB is accessible."""
    try:
        import pymongo
        from config import settings
        
        client = pymongo.MongoClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
        client.server_info()  # Will raise exception if can't connect
        print("✅ MongoDB connection successful")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("Please ensure MongoDB is running and accessible")
        return False

def main():
    """Main startup function."""
    print("🚀 Starting Genshin Impact Personal Assistant API")
    print("=" * 50)
    
    # Check all prerequisites
    if not check_requirements():
        sys.exit(1)
    
    if not check_environment():
        sys.exit(1)
    
    if not check_mongodb():
        sys.exit(1)
    
    print("=" * 50)
    print("✅ All checks passed! Starting the API server...")
    print("📖 API Documentation will be available at: http://localhost:8000/docs")
    print("🔍 Alternative docs at: http://localhost:8000/redoc")
    print("❤️  Health check at: http://localhost:8000/health")
    print("=" * 50)
    
    # Start the server
    try:
        import uvicorn
        from config import settings
        
        uvicorn.run(
            "main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 