
"""
AUREX Cosmic Glass Workspace
A futuristic deep-space nebula desktop application
with glassmorphism UI aesthetic and SQLite integration.
"""

import os
from dotenv import load_dotenv

# 🚀 Loads the key from your hidden .env file directly into system memory
load_dotenv()

from services.api_service import aurex_api
from ui.app import AurexApp

# 🔍 STARTUP & API PROVIDER DIAGNOSTICS
aurex_api.print_diagnostics()

if aurex_api.get_diagnostics()["status"] == "FAIL":
    print("\n[!] FATAL ERROR: AUREX cannot start without a valid AI provider API key.")
    print("Please add AUREX_API_KEY, GROQ_API_KEY, OPENAI_API_KEY, GITHUB_TOKEN, or HF_TOKEN to your .env file.")
    import sys
    sys.exit(1)

if __name__ == "__main__":
    app = AurexApp()
    app.mainloop()