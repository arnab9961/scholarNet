import os
from pathlib import Path
from dotenv import load_dotenv

# Base Project Directory
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

# Environment Detection (Vercel Serverless / Cloud vs Local)
IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("NOW_REGION"))
APP_ENV = os.getenv("APP_ENV", "production" if IS_VERCEL else "development").lower()
IS_PRODUCTION = APP_ENV in ("production", "prod")

# Supabase API Credentials
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = (os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_PUBLISHABLE_KEY") or "").strip()
SUPABASE_SERVICE_ROLE_KEY = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SECRET_KEY") or "").strip()
SUPABASE_JWKS_URL = os.getenv("SUPABASE_JWKS_URL", "").strip()
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "avatars").strip()

def is_supabase_configured() -> bool:
    """Returns True if valid Supabase credentials are provided."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    if "your-project-id" in SUPABASE_URL or "your-supabase" in SUPABASE_KEY:
        return False
    if "•••" in SUPABASE_KEY:
        return False
    if not (SUPABASE_URL.startswith("http://") or SUPABASE_URL.startswith("https://")):
        return False
    return True

# JWT Security Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "scholarnet_super_secret_jwt_key_2026_academic_community_auth")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0" if IS_PRODUCTION else "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "False" if IS_PRODUCTION else "True").lower() in ("true", "1", "yes")

# Directory Paths
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Safe Uploads Directory (uses /tmp on read-only serverless runtimes)
if IS_VERCEL:
    UPLOADS_DIR = Path("/tmp") / "uploads" / "avatars"
else:
    UPLOADS_DIR = STATIC_DIR / "uploads" / "avatars"

# Gracefully initialize directories without failing on read-only environments
for d in [STATIC_DIR, TEMPLATES_DIR, UPLOADS_DIR]:
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

# Ensure sub-static folders exist locally
for sub in ["css", "js", "images"]:
    try:
        (STATIC_DIR / sub).mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
