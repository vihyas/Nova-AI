#!/usr/bin/env python3
"""
NOVA AI — Intelligent Personal Assistant
Launcher Script
"""
import sys
import os
import socket
import uvicorn
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.database import init_db

def find_available_port(start_port: int = 8000, max_attempts: int = 10) -> int:
    env_port = os.getenv("PORT")
    if env_port:
        return int(env_port)
    for p in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return start_port

def main():
    print("=" * 65)
    print("🚀  NOVA AI — Intelligent Personal Assistant (v3.0.0)")
    print("    Premium AI Agent Platform | Voice | RAG | Tasks | Memory")
    print("=" * 65)
    
    # 1. Initialize SQLite Database & initial seeds
    print("📦 Initializing database & memory vault...")
    init_db()

    host = "127.0.0.1"
    port = find_available_port(8000)

    print(f"✨ NOVA AI is live and ready!")
    print(f"👉 Web Application: http://{host}:{port}")
    print(f"👉 API Documentation: http://{host}:{port}/docs")
    print(f"👉 Mode: Hybrid Multi-Agent Platform (Gemini / OpenAI / Offline)")
    print("-" * 65)

    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
