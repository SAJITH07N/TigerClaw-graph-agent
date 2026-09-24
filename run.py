"""
Convenience launcher for the TigerGraph Agentic Fraud Investigation Platform.
Usage:
    python run.py
"""

import os
import sys
import uvicorn

if __name__ == "__main__":
    # Windows consoles default to a legacy codepage (e.g. cp1252) that can't
    # encode the emoji below; force UTF-8 so the banner never crashes the launcher.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    # Ensure current project directory is in python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print("=" * 70)
    print("  🐅 Launching Agent Tiger Platform")
    print("  🌐 Dashboard: http://localhost:8000")
    print("  📚 API Docs:  http://localhost:8000/docs")
    print("=" * 70)

    uvicorn.run("app.api.server:app", host="0.0.0.0", port=8000, reload=True)
