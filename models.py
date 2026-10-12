from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150, description="Full Name of the researcher")
    university: str = Field(..., min_length=2, max_length=200, description="University / Institution affiliation")
    email: str = Field(..., min_length=5, max_length=255, description="Primary email address")
    password: str = Field(..., min_length=6, max_length=128, description="Secure password")

class UserLogin(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=1)

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    university: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    research_interests: Optional[str] = None
    cv_link: Optional[str] = None
    github_link: Optional[str] = None
    scholar_link: Optional[str] = None
    linkedin_link: Optional[str] = None
    researchgate_link: Optional[str] = None

class UserProfileResponse(BaseModel):
    id: str
    full_name: str
    university: str
    email: str
    bio: Optional[str] = ""
    avatar_url: Optional[str] = ""
    research_interests: Optional[str] = ""
    cv_link: Optional[str] = ""
    github_link: Optional[str] = ""
    scholar_link: Optional[str] = ""
    linkedin_link: Optional[str] = ""
    researchgate_link: Optional[str] = ""
    created_at: Optional[str] = None

class PostCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=500, description="Paper / Publication Title")
    abstract: str = Field(..., min_length=5, description="Abstract or publication description")
    venue: Optional[str] = Field(None, max_length=255, description="Conference, Journal, or Preprint name (e.g. NeurIPS 2026, arXiv)")
    year: Optional[int] = Field(None, description="Publication year")
    tags: Optional[str] = Field(None, description="Comma-separated tags (e.g. AI, LLM, Computer Vision)")
    paper_link: Optional[str] = Field(None, description="PDF, arXiv, or DOI link")
    code_link: Optional[str] = Field(None, description="GitHub or code repository link")
    project_link: Optional[str] = Field(None, description="Project page or demo link")
    bibtex: Optional[str] = Field(None, description="BibTeX citation block")

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=3000, description="Comment or peer review text")

class CommentResponse(BaseModel):
    id: str
    post_id: str
    user_id: str
    author_name: str
    author_university: str
    author_avatar: Optional[str] = None
    content: str
    created_at: str

class PostResponse(BaseModel):
    id: str
    user_id: str
    author_name: str
    author_university: str
    author_avatar: Optional[str] = None
    author_bio: Optional[str] = None
    title: str
    abstract: str
    venue: Optional[str] = None
    year: Optional[int] = None
    tags: Optional[str] = None
    paper_link: Optional[str] = None
    code_link: Optional[str] = None
    project_link: Optional[str] = None
    bibtex: Optional[str] = None
    likes_count: int = 0
    shares_count: int = 0
    is_liked_by_user: bool = False
    comments: List[CommentResponse] = []
    created_at: str
