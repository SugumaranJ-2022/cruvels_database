"""
Launcher script to run the FastAPI web server for the Legal AI Platform.
"""

import uvicorn
from src.config import settings

if __name__ == "__main__":
    print("Launching Legal AI Platform API & Web Interface...")
    print("Access Web Interface at: http://localhost:8000")
    print("Access API Swagger Docs at: http://localhost:8000/docs")
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000, reload=True)
