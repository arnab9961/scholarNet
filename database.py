import os
import uuid
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path

from config import (
    BASE_DIR,
    UPLOADS_DIR,
    SUPABASE_URL,
    SUPABASE_KEY,
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_STORAGE_BUCKET,
    is_supabase_configured,
)

logger = logging.getLogger("scholarnet.database")
logger.setLevel(logging.INFO)

# ==============================================================================
# SEED DATA (Academic Researchers & Publications)
# ==============================================================================
SEED_RESEARCHERS = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "full_name": "D.M. Rafiun Bin Masud (Arnab)",
        "university": "SM Technology & East West University",
        "email": "dmrafiun@gmail.com",
        # Default password: "Password123!" (hashed via bcrypt)
        "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "bio": (
            "AI Engineer at SM Technology, Dhaka, Bangladesh. Hands-on experience turning AI concepts into "
            "production-ready applications across TensorFlow, PyTorch, OpenCV, and FastAPI. Passionate about "
            "Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), AI Agents, and Spatiotemporal Prediction."
        ),
        "avatar_url": "/static/images/arnab_profile.png",
        "research_interests": "Large Language Models, Spatiotemporal Prediction, AI Agents, Computer Vision, MLOps",
        "cv_link": "https://arnab9961.github.io/data/DM_Rafiun_Bin_Masud_CV.pdf",
        "github_link": "https://github.com/arnab9961",
        "scholar_link": "https://scholar.google.com/",
        "linkedin_link": "https://www.linkedin.com/in/arnab9961/",
        "researchgate_link": "https://www.researchgate.net/profile/Dm-Masud-2/publications",
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "full_name": "Dr. Elena Rostova",
        "university": "Stanford Artificial Intelligence Laboratory",
        "email": "elena.rostova@stanford.edu",
        "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "bio": (
            "Associate Professor in Computer Science focusing on Foundation Models, Multimodal Reasoning, "
            "and Neural Representation Learning. Leading the Human-Centric AI Initiative."
        ),
        "avatar_url": "/static/images/elena_avatar.png",
        "research_interests": "Foundation Models, Multimodal AI, Deep Learning, Representation Learning",
        "cv_link": "",
        "github_link": "https://github.com/",
        "scholar_link": "https://scholar.google.com/",
        "linkedin_link": "https://linkedin.com/",
        "researchgate_link": "",
    },
]

SEED_POSTS = [
    {
        "id": "aaaaaaa1-1111-1111-1111-111111111111",
        "user_id": "11111111-1111-1111-1111-111111111111",
        "title": "Interpretable Spatiotemporal Prediction using Neural Graph Architectures",
        "abstract": (
            "Accurate prediction of dynamic spatiotemporal events is critical for intelligent transportation, "
            "climate modeling, and urban computing. We present an attention-driven graph neural network framework "
            "that preserves spatial topology while capturing long-range temporal dependencies with sub-linear complexity."
        ),
        "venue": "IEEE Transactions on Intelligent Transportation Systems",
        "year": 2026,
        "tags": "Spatiotemporal, Graph Neural Networks, AI, Deep Learning",
        "paper_link": "https://arxiv.org/abs/2301.00001",
        "code_link": "https://github.com/arnab9961",
        "project_link": "https://arnab9961.github.io/",
        "bibtex": """@article{masud2026spatiotemporal,
  title={Interpretable Spatiotemporal Prediction using Neural Graph Architectures},
  author={Masud, D. M. Rafiun Bin and Hashem, Tanzima},
  journal={IEEE Transactions on Intelligent Transportation Systems},
  year={2026}
}""",
        "likes_count": 14,
        "shares_count": 7,
    },
    {
        "id": "aaaaaaa2-2222-2222-2222-222222222222",
        "user_id": "22222222-2222-2222-2222-222222222222",
        "title": "Latent Reasoning in Multi-Agent Collaborative Systems via Fast Verification Protocols",
        "abstract": (
            "Autonomous LLM agents require reliable verification mechanisms to avoid compounding hallucinations. "
            "In this paper, we introduce a decentralized verification consensus protocol for heterogeneous agent swarms "
            "benchmarked on complex multi-step theorem proving and scientific code generation tasks."
        ),
        "venue": "NeurIPS 2026 (Oral)",
        "year": 2026,
        "tags": "AI Agents, LLMs, Reasoning, Multi-Agent Systems",
        "paper_link": "https://arxiv.org/abs/2402.00002",
        "code_link": "https://github.com/",
        "project_link": "https://stanford.edu/",
        "bibtex": """@inproceedings{rostova2026latent,
  title={Latent Reasoning in Multi-Agent Collaborative Systems via Fast Verification Protocols},
  author={Rostova, Elena and Chen, Kevin},
  booktitle={Advances in Neural Information Processing Systems (NeurIPS)},
  year={2026}
}""",
        "likes_count": 28,
        "shares_count": 12,
    },
]

SEED_COMMENTS = [
    {
        "id": "c1111111-1111-1111-1111-111111111111",
        "post_id": "aaaaaaa1-1111-1111-1111-111111111111",
        "user_id": "22222222-2222-2222-2222-222222222222",
        "content": "Outstanding formulation on the spatiotemporal adjacency matrices! How does the inference latency scale on city-scale sensor grids with >10,000 nodes?",
    },
    {
        "id": "c2222222-2222-2222-2222-222222222222",
        "post_id": "aaaaaaa1-1111-1111-1111-111111111111",
        "user_id": "11111111-1111-1111-1111-111111111111",
        "content": "Thank you Dr. Rostova! We implemented a sparse windowed partitioning strategy that bounds inference to O(N log N) without compromising boundary cross-attention.",
    },
]

# ==============================================================================
# SQLITE STORAGE BACKEND (Self-contained, reliable local engine)
# ==============================================================================
class SQLiteStorageBackend:
    def __init__(self, db_path: Optional[Path] = None):
        from config import IS_VERCEL
        if db_path is None:
            if IS_VERCEL:
                db_path = Path("/tmp") / "research_community.db"
            else:
                db_path = BASE_DIR / "research_community.db"
        self.db_path = str(db_path)
        try:
            self._init_db()
        except OSError:
            # If filesystem is read-only, safely fallback to /tmp
            self.db_path = str(Path("/tmp") / "research_community.db")
            self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    university TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    bio TEXT DEFAULT '',
                    avatar_url TEXT DEFAULT '',
                    research_interests TEXT DEFAULT '',
                    cv_link TEXT DEFAULT '',
                    github_link TEXT DEFAULT '',
                    scholar_link TEXT DEFAULT '',
                    linkedin_link TEXT DEFAULT '',
                    researchgate_link TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    abstract TEXT NOT NULL,
                    venue TEXT DEFAULT '',
                    year INTEGER,
                    tags TEXT DEFAULT '',
                    paper_link TEXT DEFAULT '',
                    code_link TEXT DEFAULT '',
                    project_link TEXT DEFAULT '',
                    bibtex TEXT DEFAULT '',
                    likes_count INTEGER DEFAULT 0,
                    shares_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id TEXT PRIMARY KEY,
                    post_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS post_likes (
                    id TEXT PRIMARY KEY,
                    post_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(post_id, user_id),
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE
                )
            """)

            # Seed researchers if empty
            cursor.execute("SELECT COUNT(*) FROM profiles")
            if cursor.fetchone()[0] == 0:
                now_str = datetime.now(timezone.utc).isoformat()
                for r in SEED_RESEARCHERS:
                    cursor.execute("""
                        INSERT INTO profiles (
                            id, full_name, university, email, password_hash, bio,
                            avatar_url, research_interests, cv_link, github_link,
                            scholar_link, linkedin_link, researchgate_link, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        r["id"], r["full_name"], r["university"], r["email"], r["password_hash"],
                        r["bio"], r["avatar_url"], r["research_interests"], r["cv_link"],
                        r["github_link"], r["scholar_link"], r["linkedin_link"],
                        r["researchgate_link"], now_str, now_str
                    ))

                for p in SEED_POSTS:
                    cursor.execute("""
                        INSERT INTO posts (
                            id, user_id, title, abstract, venue, year, tags,
                            paper_link, code_link, project_link, bibtex, likes_count,
                            shares_count, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        p["id"], p["user_id"], p["title"], p["abstract"], p["venue"],
                        p["year"], p["tags"], p["paper_link"], p["code_link"],
                        p["project_link"], p["bibtex"], p["likes_count"], p["shares_count"],
                        now_str, now_str
                    ))

                for c in SEED_COMMENTS:
                    cursor.execute("""
                        INSERT INTO comments (id, post_id, user_id, content, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        c["id"], c["post_id"], c["user_id"], c["content"], now_str
                    ))

            conn.commit()

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profiles WHERE lower(email) = lower(?)", (email.strip(),))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profiles WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        user_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO profiles (
                    id, full_name, university, email, password_hash, bio,
                    avatar_url, research_interests, cv_link, github_link,
                    scholar_link, linkedin_link, researchgate_link, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                data["full_name"],
                data["university"],
                data["email"].strip().lower(),
                data["password_hash"],
                data.get("bio", ""),
                data.get("avatar_url", "/static/images/default-avatar.png"),
                data.get("research_interests", ""),
                data.get("cv_link", ""),
                data.get("github_link", ""),
                data.get("scholar_link", ""),
                data.get("linkedin_link", ""),
                data.get("researchgate_link", ""),
                now_str,
                now_str
            ))
            conn.commit()
        return self.get_user_by_id(user_id)

    def update_user_profile(self, user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        now_str = datetime.now(timezone.utc).isoformat()
        fields = []
        values = []
        for key in [
            "full_name", "university", "bio", "avatar_url", "research_interests",
            "cv_link", "github_link", "scholar_link", "linkedin_link", "researchgate_link"
        ]:
            if key in data and data[key] is not None:
                fields.append(f"{key} = ?")
                values.append(data[key])

        if not fields:
            return self.get_user_by_id(user_id)

        fields.append("updated_at = ?")
        values.append(now_str)
        values.append(user_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = f"UPDATE profiles SET {', '.join(fields)} WHERE id = ?"
            cursor.execute(query, tuple(values))
            conn.commit()

        return self.get_user_by_id(user_id)

    def get_posts(self, search: Optional[str] = None, tag: Optional[str] = None, user_filter: Optional[str] = None, current_user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    p.*,
                    u.full_name as author_name,
                    u.university as author_university,
                    u.avatar_url as author_avatar,
                    u.bio as author_bio
                FROM posts p
                JOIN profiles u ON p.user_id = u.id
                WHERE 1=1
            """
            params = []

            if user_filter:
                query += " AND p.user_id = ?"
                params.append(user_filter)

            if tag and tag.lower() != "all":
                query += " AND lower(p.tags) LIKE ?"
                params.append(f"%{tag.lower()}%")

            if search:
                term = f"%{search.lower()}%"
                query += " AND (lower(p.title) LIKE ? OR lower(p.abstract) LIKE ? OR lower(u.full_name) LIKE ? OR lower(u.university) LIKE ?)"
                params.extend([term, term, term, term])

            query += " ORDER BY p.created_at DESC"
            cursor.execute(query, tuple(params))
            posts = [dict(row) for row in cursor.fetchall()]

            # Fetch comments and like status for each post
            for post in posts:
                post["comments"] = self.get_comments(post["id"])
                post["is_liked_by_user"] = False
                if current_user_id:
                    cursor.execute("SELECT 1 FROM post_likes WHERE post_id = ? AND user_id = ?", (post["id"], current_user_id))
                    post["is_liked_by_user"] = cursor.fetchone() is not None

            return posts

    def get_post_by_id(self, post_id: str, current_user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.*,
                    u.full_name as author_name,
                    u.university as author_university,
                    u.avatar_url as author_avatar,
                    u.bio as author_bio
                FROM posts p
                JOIN profiles u ON p.user_id = u.id
                WHERE p.id = ?
            """, (post_id,))
            row = cursor.fetchone()
            if not row:
                return None
            post = dict(row)
            post["comments"] = self.get_comments(post_id)
            post["is_liked_by_user"] = False
            if current_user_id:
                cursor.execute("SELECT 1 FROM post_likes WHERE post_id = ? AND user_id = ?", (post_id, current_user_id))
                post["is_liked_by_user"] = cursor.fetchone() is not None
            return post

    def create_post(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        post_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()
        current_year = data.get("year") or datetime.now().year
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO posts (
                    id, user_id, title, abstract, venue, year, tags,
                    paper_link, code_link, project_link, bibtex, likes_count,
                    shares_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
            """, (
                post_id,
                user_id,
                data["title"],
                data["abstract"],
                data.get("venue", ""),
                current_year,
                data.get("tags", ""),
                data.get("paper_link", ""),
                data.get("code_link", ""),
                data.get("project_link", ""),
                data.get("bibtex", ""),
                now_str,
                now_str
            ))
            conn.commit()
        return self.get_post_by_id(post_id, current_user_id=user_id)

    def delete_post(self, post_id: str, user_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM posts WHERE id = ? AND user_id = ?", (post_id, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_comments(self, post_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    c.id, c.post_id, c.user_id, c.content, c.created_at,
                    u.full_name as author_name,
                    u.university as author_university,
                    u.avatar_url as author_avatar
                FROM comments c
                JOIN profiles u ON c.user_id = u.id
                WHERE c.post_id = ?
                ORDER BY c.created_at ASC
            """, (post_id,))
            return [dict(row) for row in cursor.fetchall()]

    def create_comment(self, post_id: str, user_id: str, content: str) -> Dict[str, Any]:
        comment_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO comments (id, post_id, user_id, content, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (comment_id, post_id, user_id, content, now_str))
            conn.commit()
            cursor.execute("""
                SELECT 
                    c.id, c.post_id, c.user_id, c.content, c.created_at,
                    u.full_name as author_name,
                    u.university as author_university,
                    u.avatar_url as author_avatar
                FROM comments c
                JOIN profiles u ON c.user_id = u.id
                WHERE c.id = ?
            """, (comment_id,))
            return dict(cursor.fetchone())

    def toggle_like(self, post_id: str, user_id: str) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM post_likes WHERE post_id = ? AND user_id = ?", (post_id, user_id))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("DELETE FROM post_likes WHERE post_id = ? AND user_id = ?", (post_id, user_id))
                cursor.execute("UPDATE posts SET likes_count = MAX(0, likes_count - 1) WHERE id = ?", (post_id,))
                is_liked = False
            else:
                like_id = str(uuid.uuid4())
                now_str = datetime.now(timezone.utc).isoformat()
                cursor.execute("INSERT INTO post_likes (id, post_id, user_id, created_at) VALUES (?, ?, ?, ?)", (like_id, post_id, user_id, now_str))
                cursor.execute("UPDATE posts SET likes_count = likes_count + 1 WHERE id = ?", (post_id,))
                is_liked = True

            conn.commit()
            cursor.execute("SELECT likes_count FROM posts WHERE id = ?", (post_id,))
            count = cursor.fetchone()[0]
            return {"liked": is_liked, "likes_count": count}

    def increment_share(self, post_id: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE posts SET shares_count = shares_count + 1 WHERE id = ?", (post_id,))
            conn.commit()
            cursor.execute("SELECT shares_count FROM posts WHERE id = ?", (post_id,))
            row = cursor.fetchone()
            return row[0] if row else 1

    def get_all_researchers(self, limit: int = 15) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, full_name, university, avatar_url, research_interests
                FROM profiles
                ORDER BY created_at ASC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]


# ==============================================================================
# SUPABASE STORAGE BACKEND (Remote PostgreSQL + Storage via Supabase Python SDK)
# ==============================================================================
class SupabaseStorageBackend:
    def __init__(self):
        from supabase import create_client, Client
        active_key = (
            SUPABASE_SERVICE_ROLE_KEY 
            if (SUPABASE_SERVICE_ROLE_KEY and "•••" not in SUPABASE_SERVICE_ROLE_KEY) 
            else SUPABASE_KEY
        )
        self.client: Client = create_client(SUPABASE_URL, active_key)
        logger.info("Connected to Supabase client successfully: %s", SUPABASE_URL)

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            res = self.client.table("profiles").select("*").ilike("email", email.strip()).limit(1).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except Exception as e:
            logger.error("Supabase get_user_by_email error: %s", e)
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            res = self.client.table("profiles").select("*").eq("id", user_id).limit(1).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except Exception as e:
            logger.error("Supabase get_user_by_id error: %s", e)
            return None

    def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        user_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()
        row = {
            "id": user_id,
            "full_name": data["full_name"],
            "university": data["university"],
            "email": data["email"].strip().lower(),
            "password_hash": data["password_hash"],
            "bio": data.get("bio", ""),
            "avatar_url": data.get("avatar_url", "/static/images/default-avatar.png"),
            "research_interests": data.get("research_interests", ""),
            "cv_link": data.get("cv_link", ""),
            "github_link": data.get("github_link", ""),
            "scholar_link": data.get("scholar_link", ""),
            "linkedin_link": data.get("linkedin_link", ""),
            "researchgate_link": data.get("researchgate_link", ""),
            "created_at": now_str,
            "updated_at": now_str,
        }
        res = self.client.table("profiles").insert(row).execute()
        return res.data[0] if res.data else row

    def update_user_profile(self, user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        now_str = datetime.now(timezone.utc).isoformat()
        update_data = {k: v for k, v in data.items() if v is not None}
        update_data["updated_at"] = now_str
        res = self.client.table("profiles").update(update_data).eq("id", user_id).execute()
        return res.data[0] if res.data else self.get_user_by_id(user_id)

    def get_posts(self, search: Optional[str] = None, tag: Optional[str] = None, user_filter: Optional[str] = None, current_user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            query = self.client.table("posts").select("*, profiles!user_id(full_name, university, avatar_url, bio)")
            if user_filter:
                query = query.eq("user_id", user_filter)
            if tag and tag.lower() != "all":
                query = query.ilike("tags", f"%{tag}%")
            if search:
                query = query.or_(f"title.ilike.%{search}%,abstract.ilike.%{search}%")

            query = query.order("created_at", desc=True)
            res = query.execute()
            posts = []
            for item in res.data or []:
                profile = item.get("profiles") or {}
                post = {
                    **item,
                    "author_name": profile.get("full_name", "Researcher"),
                    "author_university": profile.get("university", "Institution"),
                    "author_avatar": profile.get("avatar_url", "/static/images/default-avatar.png"),
                    "author_bio": profile.get("bio", ""),
                    "comments": self.get_comments(item["id"]),
                    "is_liked_by_user": False,
                }
                if current_user_id:
                    likes_res = self.client.table("post_likes").select("id").eq("post_id", item["id"]).eq("user_id", current_user_id).execute()
                    post["is_liked_by_user"] = bool(likes_res.data and len(likes_res.data) > 0)
                posts.append(post)
            return posts
        except Exception as e:
            logger.error("Supabase get_posts error: %s", e)
            return []

    def get_post_by_id(self, post_id: str, current_user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            res = self.client.table("posts").select("*, profiles!user_id(full_name, university, avatar_url, bio)").eq("id", post_id).limit(1).execute()
            if not res.data:
                return None
            item = res.data[0]
            profile = item.get("profiles") or {}
            post = {
                **item,
                "author_name": profile.get("full_name", "Researcher"),
                "author_university": profile.get("university", "Institution"),
                "author_avatar": profile.get("avatar_url", "/static/images/default-avatar.png"),
                "author_bio": profile.get("bio", ""),
                "comments": self.get_comments(post_id),
                "is_liked_by_user": False,
            }
            if current_user_id:
                likes_res = self.client.table("post_likes").select("id").eq("post_id", post_id).eq("user_id", current_user_id).execute()
                post["is_liked_by_user"] = bool(likes_res.data and len(likes_res.data) > 0)
            return post
        except Exception as e:
            logger.error("Supabase get_post_by_id error: %s", e)
            return None

    def create_post(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        post_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()
        current_year = data.get("year") or datetime.now().year
        row = {
            "id": post_id,
            "user_id": user_id,
            "title": data["title"],
            "abstract": data["abstract"],
            "venue": data.get("venue", ""),
            "year": current_year,
            "tags": data.get("tags", ""),
            "paper_link": data.get("paper_link", ""),
            "code_link": data.get("code_link", ""),
            "project_link": data.get("project_link", ""),
            "bibtex": data.get("bibtex", ""),
            "likes_count": 0,
            "shares_count": 0,
            "created_at": now_str,
            "updated_at": now_str,
        }
        self.client.table("posts").insert(row).execute()
        return self.get_post_by_id(post_id, current_user_id=user_id)

    def delete_post(self, post_id: str, user_id: str) -> bool:
        try:
            res = self.client.table("posts").delete().eq("id", post_id).eq("user_id", user_id).execute()
            return bool(res.data and len(res.data) > 0)
        except Exception:
            return False

    def get_comments(self, post_id: str) -> List[Dict[str, Any]]:
        try:
            res = self.client.table("comments").select("*, profiles!user_id(full_name, university, avatar_url)").eq("post_id", post_id).order("created_at", desc=False).execute()
            comments = []
            for item in res.data or []:
                profile = item.get("profiles") or {}
                comments.append({
                    "id": item["id"],
                    "post_id": item["post_id"],
                    "user_id": item["user_id"],
                    "content": item["content"],
                    "created_at": item["created_at"],
                    "author_name": profile.get("full_name", "Researcher"),
                    "author_university": profile.get("university", "Institution"),
                    "author_avatar": profile.get("avatar_url", "/static/images/default-avatar.png"),
                })
            return comments
        except Exception as e:
            logger.error("Supabase get_comments error: %s", e)
            return []

    def create_comment(self, post_id: str, user_id: str, content: str) -> Dict[str, Any]:
        comment_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()
        row = {
            "id": comment_id,
            "post_id": post_id,
            "user_id": user_id,
            "content": content,
            "created_at": now_str,
        }
        self.client.table("comments").insert(row).execute()
        user = self.get_user_by_id(user_id) or {}
        return {
            **row,
            "author_name": user.get("full_name", "Researcher"),
            "author_university": user.get("university", "Institution"),
            "author_avatar": user.get("avatar_url", "/static/images/default-avatar.png"),
        }

    def toggle_like(self, post_id: str, user_id: str) -> Dict[str, Any]:
        try:
            existing = self.client.table("post_likes").select("id").eq("post_id", post_id).eq("user_id", user_id).execute()
            if existing.data and len(existing.data) > 0:
                self.client.table("post_likes").delete().eq("post_id", post_id).eq("user_id", user_id).execute()
                # decrement count
                post = self.client.table("posts").select("likes_count").eq("id", post_id).single().execute()
                current_count = max(0, (post.data.get("likes_count", 1) - 1))
                self.client.table("posts").update({"likes_count": current_count}).eq("id", post_id).execute()
                return {"liked": False, "likes_count": current_count}
            else:
                self.client.table("post_likes").insert({
                    "id": str(uuid.uuid4()),
                    "post_id": post_id,
                    "user_id": user_id,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }).execute()
                post = self.client.table("posts").select("likes_count").eq("id", post_id).single().execute()
                current_count = post.data.get("likes_count", 0) + 1
                self.client.table("posts").update({"likes_count": current_count}).eq("id", post_id).execute()
                return {"liked": True, "likes_count": current_count}
        except Exception as e:
            logger.error("Supabase toggle_like error: %s", e)
            return {"liked": False, "likes_count": 0}

    def increment_share(self, post_id: str) -> int:
        try:
            post = self.client.table("posts").select("shares_count").eq("id", post_id).single().execute()
            current_count = (post.data.get("shares_count") or 0) + 1
            self.client.table("posts").update({"shares_count": current_count}).eq("id", post_id).execute()
            return current_count
        except Exception:
            return 1

    def get_all_researchers(self, limit: int = 15) -> List[Dict[str, Any]]:
        try:
            res = self.client.table("profiles").select("id, full_name, university, avatar_url, research_interests").limit(limit).execute()
            return res.data or []
        except Exception:
            return []


# ==============================================================================
# SINGLETON STORAGE FACTORY (Seamless Dual Engine)
# ==============================================================================
_db_instance = None

def get_db():
    global _db_instance
    if _db_instance is not None:
        return _db_instance

    if is_supabase_configured():
        try:
            logger.info("Initializing Supabase Storage Engine with configured credentials...")
            candidate = SupabaseStorageBackend()
            # Verify that schema tables exist in the Supabase project
            candidate.client.table("profiles").select("id").limit(1).execute()
            _db_instance = candidate
            print(">>> [DB ENGINE] Successfully connected and verified Supabase PostgreSQL database tables!")
            return _db_instance
        except Exception as exc:
            error_str = str(exc)
            if "PGRST205" in error_str or "schema cache" in error_str or "Could not find the table" in error_str:
                print("\n" + "="*75)
                print(">>> [SUPABASE NOTICE] Connected to your Supabase project (ccivcmvwhjireufzuvxs)!")
                print(">>> The database tables ('profiles', 'posts', etc.) have not been created yet.")
                print(">>> TO CREATE THE TABLES IN SUPABASE:")
                print(">>> 1. Open: https://supabase.com/dashboard/project/ccivcmvwhjireufzuvxs/sql/new")
                print(">>> 2. Copy the content from 'schema.sql' and click 'Run'.")
                print(">>> Running on local database (research_community.db) until tables are created.")
                print("="*75 + "\n")
            else:
                logger.warning("Could not connect to Supabase: %s. Falling back to local SQLite engine.", exc)
                print(f">>> [DB ENGINE] Supabase connection failed ({exc}). Falling back to local SQLite engine.")

    logger.info("Using local SQLite Storage Engine (database.sqlite).")
    print(">>> [DB ENGINE] Running with local SQLite database engine (research_community.db).")
    _db_instance = SQLiteStorageBackend()
    return _db_instance
