"""
AUREX Cosmic Glass Workspace
A futuristic deep-space nebula desktop application
with glassmorphism UI aesthetic and SQLite integration.
"""

from ui.app import AurexApp
import os
from dotenv import load_dotenv

# 🚀 Loads the key from your hidden .env file directly into system memory
load_dotenv()

if __name__ == "__main__":
    app = AurexApp()
    app.mainloop()
