import sys
from pathlib import Path

# Ensure project root is in sys.path for serverless execution on Vercel
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from main import app

# Export app for Vercel serverless function handler
handler = app
