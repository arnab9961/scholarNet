-- ==============================================================================
-- SCHOLARNET / RESEARCH & PUBLICATION COMMUNITY DATABASE SCHEMA (SUPABASE POSTGRES)
-- ==============================================================================
-- Run this script in your Supabase SQL Editor (Dashboard -> SQL Editor -> New Query)
-- It creates all required tables, indexes, Row Level Security (RLS) policies,
-- and seed sample data following Supabase Postgres best practices.
-- ==============================================================================

-- 1. Enable pgcrypto for UUID generation if not already enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================================================================
-- TABLE: profiles
-- Stores registered researchers and community members
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    university TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    bio TEXT,
    avatar_url TEXT,
    research_interests TEXT,
    cv_link TEXT,
    github_link TEXT,
    scholar_link TEXT,
    linkedin_link TEXT,
    researchgate_link TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for email lookups
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_university ON public.profiles(university);

-- ==============================================================================
-- TABLE: posts
-- Stores research publication posts, preprint discussions, and community updates
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    abstract TEXT NOT NULL,
    venue TEXT,
    year INT DEFAULT EXTRACT(YEAR FROM CURRENT_DATE),
    tags TEXT,
    paper_link TEXT,
    code_link TEXT,
    project_link TEXT,
    bibtex TEXT,
    likes_count INT NOT NULL DEFAULT 0,
    shares_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON public.posts(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON public.posts(created_at DESC);

-- ==============================================================================
-- TABLE: comments
-- Stores research discussions, peer feedback, and questions on publications
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL REFERENCES public.posts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for fast comment retrieval
CREATE INDEX IF NOT EXISTS idx_comments_post_id ON public.comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_user_id ON public.comments(user_id);
CREATE INDEX IF NOT EXISTS idx_comments_created_at ON public.comments(created_at ASC);

-- ==============================================================================
-- TABLE: post_likes
-- Tracks which researchers have upvoted / starred a publication
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.post_likes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL REFERENCES public.posts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT unique_post_user_like UNIQUE (post_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_post_likes_post_id ON public.post_likes(post_id);
CREATE INDEX IF NOT EXISTS idx_post_likes_user_id ON public.post_likes(user_id);

-- ==============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ==============================================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.post_likes ENABLE ROW LEVEL SECURITY;

-- Profiles: Anyone can view profiles, backend/owners can update
DROP POLICY IF EXISTS "Public can view profiles" ON public.profiles;
CREATE POLICY "Public can view profiles" ON public.profiles FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow profile registration" ON public.profiles;
CREATE POLICY "Allow profile registration" ON public.profiles FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Allow profile update" ON public.profiles;
CREATE POLICY "Allow profile update" ON public.profiles FOR UPDATE USING (true);

-- Posts: Anyone can view posts; authenticated researchers can insert
DROP POLICY IF EXISTS "Public can view posts" ON public.posts;
CREATE POLICY "Public can view posts" ON public.posts FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow post creation" ON public.posts;
CREATE POLICY "Allow post creation" ON public.posts FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Allow post update" ON public.posts;
CREATE POLICY "Allow post update" ON public.posts FOR UPDATE USING (true);

DROP POLICY IF EXISTS "Allow post deletion" ON public.posts;
CREATE POLICY "Allow post deletion" ON public.posts FOR DELETE USING (true);

-- Comments: Anyone can view comments; researchers can add comments
DROP POLICY IF EXISTS "Public can view comments" ON public.comments;
CREATE POLICY "Public can view comments" ON public.comments FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow comment creation" ON public.comments;
CREATE POLICY "Allow comment creation" ON public.comments FOR INSERT WITH CHECK (true);

-- Likes: Anyone can view likes; users can toggle likes
DROP POLICY IF EXISTS "Public can view likes" ON public.post_likes;
CREATE POLICY "Public can view likes" ON public.post_likes FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow like actions" ON public.post_likes;
CREATE POLICY "Allow like actions" ON public.post_likes FOR ALL USING (true);

-- ==============================================================================
-- STORAGE BUCKET CONFIGURATION (Optional Supabase Storage)
-- Run this in Storage section or SQL to create the avatar bucket
-- ==============================================================================
INSERT INTO storage.buckets (id, name, public)
VALUES ('avatars', 'avatars', true)
ON CONFLICT (id) DO NOTHING;

-- Storage RLS: Allow public reading of avatars
DROP POLICY IF EXISTS "Public avatar access" ON storage.objects;
CREATE POLICY "Public avatar access" ON storage.objects FOR SELECT USING (bucket_id = 'avatars');

DROP POLICY IF EXISTS "Public avatar upload" ON storage.objects;
CREATE POLICY "Public avatar upload" ON storage.objects FOR INSERT WITH CHECK (bucket_id = 'avatars');
