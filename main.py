"""
Aurex Cosmic Glass Workspace
A futuristic deep-space nebula desktop application
with glassmorphism UI aesthetic and SQLite integration.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Robust .env loading for both Python interpreter and packaged PyInstaller .exe
app_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
env_file = app_dir / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
else:
    load_dotenv()

from services.api_service import aurex_api
from ui.app import AurexApp

# STARTUP & API PROVIDER DIAGNOSTICS
aurex_api.print_diagnostics()

if aurex_api.get_diagnostics()["status"] == "FAIL":
    print("\n[!] FATAL ERROR: Aurex cannot start without a valid AI provider API key.")
    print("Please add NVIDIA_API_KEY, GROQ_API_KEY, OPENAI_API_KEY, GITHUB_TOKEN, or HF_TOKEN to your .env file.")
    import sys
    sys.exit(1)

if __name__ == "__main__":
    app = AurexApp()
    app.mainloop()