import os
import shutil
import uuid
import base64
import logging
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, Request, Response, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from config import (
    STATIC_DIR,
    TEMPLATES_DIR,
    UPLOADS_DIR,
    HOST,
    PORT,
    DEBUG,
    APP_ENV,
    IS_PRODUCTION,
    IS_VERCEL,
    SUPABASE_URL,
    SUPABASE_KEY,
    SUPABASE_STORAGE_BUCKET,
    is_supabase_configured,
)
from models import (
    UserRegister,
    UserLogin,
    UserProfileUpdate,
    UserProfileResponse,
    PostCreate,
    PostResponse,
    CommentCreate,
    CommentResponse,
)
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_user_optional,
)
from database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scholarnet")

# Initialize FastAPI application
app = FastAPI(
    title="ScholarNet | Research & Publication Community",
    description="An academic research dissemination and peer publication platform.",
    version="1.0.0",
    docs_url="/docs" if not IS_PRODUCTION else None,
    redoc_url="/redoc" if not IS_PRODUCTION else None,
)

# ==============================================================================
# PRODUCTION MIDDLEWARE & SECURITY HEADERS
# ==============================================================================
# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Mount Static Files and Templates
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Explicit Favicon Route
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = STATIC_DIR / "images" / "favicon.png"
    if favicon_path.exists():
        return FileResponse(favicon_path, media_type="image/png")
    return Response(status_code=204)

# Production Health Check
@app.get("/api/health", tags=["System"])
async def health_check():
    db = get_db()
    return {
        "status": "healthy",
        "service": "ScholarNet Academic Platform",
        "environment": APP_ENV,
        "is_vercel": IS_VERCEL,
        "supabase_configured": is_supabase_configured(),
        "version": "1.0.0",
    }

# ==============================================================================
# HTML PAGE ROUTES
# ==============================================================================
@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Academic Home Page: research feed, mission banner, active scholars."""
    db = get_db()
    researchers = db.get_all_researchers(limit=10)
    current_user = await get_current_user_optional(request)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "researchers": researchers,
            "current_user": current_user,
            "supabase_active": is_supabase_configured(),
        },
    )

@app.get("/profile/{user_id}", response_class=HTMLResponse)
async def user_profile_page(user_id: str, request: Request):
    """Public Academic Researcher Profile (strictly styled after arnab9961.github.io)."""
    db = get_db()
    profile = db.get_user_by_id(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Researcher profile not found")

    current_user = await get_current_user_optional(request)
    current_uid = current_user.get("sub") if current_user else None
    posts = db.get_posts(user_filter=user_id, current_user_id=current_uid)

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "profile": profile,
            "posts": posts,
            "current_user": current_user,
            "is_owner": current_uid == user_id,
        },
    )

@app.get("/my-profile")
async def my_profile_redirect(request: Request):
    """Redirects authenticated user to their academic profile."""
    current_user = await get_current_user_optional(request)
    if not current_user:
        return RedirectResponse(url="/?login=true")
    return RedirectResponse(url=f"/profile/{current_user['sub']}")

# ==============================================================================
# AUTHENTICATION API ROUTES
# ==============================================================================
@app.post("/api/auth/register")
async def register(user_data: UserRegister, request: Request, response: Response):
    """Registers a new researcher with full name, university, email, and password."""
    db = get_db()
    existing = db.get_user_by_email(user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An academic profile with this email address already exists.",
        )

    hashed_pw = hash_password(user_data.password)
    user_record = db.create_user({
        "full_name": user_data.full_name,
        "university": user_data.university,
        "email": user_data.email,
        "password_hash": hashed_pw,
        "avatar_url": "/static/images/default-avatar.png",
    })

    # Issue JWT token
    token = create_access_token({
        "sub": user_record["id"],
        "email": user_record["email"],
        "name": user_record["full_name"],
        "university": user_record["university"],
    })

    # Secure Cookie Settings for Production & HTTPS
    is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=60 * 60 * 24 * 7,  # 7 days
        samesite="lax",
        secure=is_https or IS_PRODUCTION,
    )

    safe_user = {k: v for k, v in user_record.items() if k != "password_hash"}
    return {"token": token, "user": safe_user, "message": "Researcher registration successful!"}

@app.post("/api/auth/login")
async def login(credentials: UserLogin, request: Request, response: Response):
    """Authenticates researcher and issues JWT."""
    db = get_db()
    user = db.get_user_by_email(credentials.email)
    if not user or not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token({
        "sub": user["id"],
        "email": user["email"],
        "name": user["full_name"],
        "university": user["university"],
    })

    is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax",
        secure=is_https or IS_PRODUCTION,
    )

    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    return {"token": token, "user": safe_user, "message": "Sign in successful!"}

@app.post("/api/auth/logout")
async def logout(response: Response):
    """Logs out researcher by clearing the session cookie."""
    response.delete_cookie(key="access_token")
    return {"message": "Signed out successfully."}

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Returns currently authenticated researcher profile."""
    db = get_db()
    user = db.get_user_by_id(current_user["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")
    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    return safe_user

# ==============================================================================
# PROFILE MANAGEMENT & AVATAR UPLOAD
# ==============================================================================
@app.get("/api/profile")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Retrieves profile of the authenticated user."""
    db = get_db()
    user = db.get_user_by_id(current_user["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")
    return {k: v for k, v in user.items() if k != "password_hash"}

@app.put("/api/profile")
async def update_profile(
    update_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Updates researcher profile (name, affiliation, bio, research interests, links)."""
    db = get_db()
    updated = db.update_user_profile(current_user["sub"], update_data.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=400, detail="Profile update could not be completed.")
    return {k: v for k, v in updated.items() if k != "password_hash"}

@app.post("/api/profile/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Uploads a profile picture with resilient storage (Supabase / local / data URI fallback)."""
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid image format. Please upload JPG, PNG, WEBP, or GIF.",
        )

    ext = Path(file.filename or "avatar.png").suffix.lower()
    if not ext or ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        ext = ".png"

    filename = f"{current_user['sub']}_{uuid.uuid4().hex[:8]}{ext}"
    content = await file.read()

    if len(content) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(status_code=400, detail="Image file exceeds maximum 5MB size limit.")

    avatar_url = None

    # 1. Attempt upload to Supabase Storage if configured
    if is_supabase_configured():
        try:
            from supabase import create_client
            active_key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY
            supabase_client = create_client(SUPABASE_URL, active_key)
            bucket = SUPABASE_STORAGE_BUCKET or "avatars"
            supabase_client.storage.from_(bucket).upload(
                path=filename,
                file=content,
                file_options={"content-type": file.content_type, "upsert": "true"},
            )
            public_url = supabase_client.storage.from_(bucket).get_public_url(filename)
            if public_url:
                avatar_url = public_url
        except Exception as e:
            logger.warning("Supabase storage upload skipped or failed: %s. Using file fallback.", e)

    # 2. Local File Fallback (or Data URI if filesystem is read-only)
    if not avatar_url:
        try:
            dest_path = UPLOADS_DIR / filename
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as f:
                f.write(content)
            avatar_url = f"/static/uploads/avatars/{filename}"
        except OSError:
            # Read-only serverless fallback: Store as Base64 Data URL
            encoded = base64.b64encode(content).decode("utf-8")
            avatar_url = f"data:{file.content_type};base64,{encoded}"

    # Update database record
    db = get_db()
    db.update_user_profile(current_user["sub"], {"avatar_url": avatar_url})

    return {"avatar_url": avatar_url, "message": "Avatar uploaded successfully"}

# ==============================================================================
# POSTS & RESEARCH PUBLICATIONS API
# ==============================================================================
@app.get("/api/posts")
async def list_posts(
    search: Optional[str] = None,
    tag: Optional[str] = None,
    user_id: Optional[str] = None,
    request: Request = None,
):
    """Fetches list of publications, preprints, and research posts with comments and like counts."""
    db = get_db()
    current_user = await get_current_user_optional(request) if request else None
    current_uid = current_user.get("sub") if current_user else None
    posts = db.get_posts(search=search, tag=tag, user_filter=user_id, current_user_id=current_uid)
    return posts

@app.get("/api/posts/{post_id}")
async def get_post(post_id: str, request: Request):
    """Fetches a single publication by ID."""
    db = get_db()
    current_user = await get_current_user_optional(request)
    current_uid = current_user.get("sub") if current_user else None
    post = db.get_post_by_id(post_id, current_user_id=current_uid)
    if not post:
        raise HTTPException(status_code=404, detail="Publication post not found")
    return post

@app.post("/api/posts")
async def create_post(
    post_data: PostCreate,
    current_user: dict = Depends(get_current_user),
):
    """Publishes a new research paper or discussion."""
    db = get_db()
    new_post = db.create_post(current_user["sub"], post_data.model_dump())
    return new_post

@app.delete("/api/posts/{post_id}")
async def delete_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Deletes a publication authored by the current user."""
    db = get_db()
    success = db.delete_post(post_id, current_user["sub"])
    if not success:
        raise HTTPException(status_code=403, detail="Unable to delete post or not authorized.")
    return {"message": "Publication post deleted successfully"}

# ==============================================================================
# ENGAGEMENT: LIKES, SHARES & COMMENTS
# ==============================================================================
@app.post("/api/posts/{post_id}/like")
async def toggle_like_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Toggles like / star on a publication."""
    db = get_db()
    result = db.toggle_like(post_id, current_user["sub"])
    return result

@app.post("/api/posts/{post_id}/share")
async def share_post(post_id: str):
    """Increments publication share counter."""
    db = get_db()
    new_count = db.increment_share(post_id)
    return {"shares_count": new_count, "message": "Publication shared"}

@app.get("/api/posts/{post_id}/comments")
async def get_post_comments(post_id: str):
    """Returns comments on a publication."""
    db = get_db()
    return db.get_comments(post_id)

@app.post("/api/posts/{post_id}/comment")
async def add_post_comment(
    post_id: str,
    comment_data: CommentCreate,
    current_user: dict = Depends(get_current_user),
):
    """Adds a peer comment or feedback to a publication."""
    db = get_db()
    comment = db.create_comment(post_id, current_user["sub"], comment_data.content)
    return comment

@app.get("/api/researchers")
async def list_researchers():
    """Lists community researchers."""
    db = get_db()
    return db.get_all_researchers(limit=25)

# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    print(f"\n========================================================")
    print(f" ScholarNet - Research & Publication Community Server   ")
    print(f" URL: http://{HOST}:{PORT}                              ")
    print(f" Environment: {APP_ENV}                                 ")
    print(f" Supabase Configured: {is_supabase_configured()}        ")
    print(f"========================================================\n")
    uvicorn.run("main:app", host=HOST, port=PORT, reload=DEBUG)
