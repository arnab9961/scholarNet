# ScholarNet - Research & Publication Community

A full-stack research and publication community platform built with **FastAPI**, **HTML5/CSS3/Vanilla JS**, and **Supabase (PostgreSQL)**, meticulously styled after the academic researcher theme of [arnab9961.github.io](https://arnab9961.github.io/) (Jon Barron academic portfolio format).

---

## 🌟 Key Features

1. **Academic Design System**:
   - Replicates the typography and aesthetic of [arnab9961.github.io](https://arnab9961.github.io/).
   - Uses `Lato` and `Verdana` fonts, deep maroon (`#800000`) link colors, warm amber (`#f09228`) hover states, and academic badge labels (`.label-pps`, `.label-lab`, `.label-due`, `.label-lecture`).
   - Circular author profile photos with smooth `.hoverZoomLink` micro-interactions.
   - Clean publication cards with paper titles (`<papertitle>`), venue, year, abstract, and bibtex snippets.

2. **User Authentication & Academic Profile Management**:
   - **Registration**: Full Name, University / Institution Affiliation, Primary Email Address, Password (hashed securely via `bcrypt`).
   - **Login**: Email + Password with secure HttpOnly JWT cookie sessions.
   - **Profile Customization**:
     - Edit full name, university affiliation, and biographical research description.
     - Add research interests and tags (e.g. LLMs, Spatiotemporal Prediction, AI Agents, MLOps).
     - **Profile Picture Upload**: Upload JPEG, PNG, or WEBP photos with real-time preview and server storage (with automatic Supabase Storage sync and Base64 data URL fallback).
     - External academic links: CV / Resume PDF, GitHub, Google Scholar, LinkedIn, ResearchGate.
   - **Public Researcher Portfolio**: Each user has their own URL `/profile/{user_id}` displaying their academic background and published papers.

3. **Community Feed & Research Dissemination**:
   - **Home Page Feed**: Displays publications and research posts from all community members.
   - **Publish Research**: Add paper title, venue (e.g. NeurIPS, IEEE, arXiv), abstract, tags, PDF link, code repository, project link, and formatted BibTeX.
   - **Peer Discussion & Comments**: Interactive comments thread on every publication.
   - **Share Publication**:
     - Instant share modal with direct link copying.
     - One-click share to X / Twitter and LinkedIn.
     - BibTeX citation generator with 1-click copy button.
     - Live share counter.
   - **Upvotes / Stars**: Toggle upvotes on papers with live counters.
   - **Filtering & Search**: Live keyword search across titles, abstracts, authors, and universities, plus topic filtering tags.

4. **Production-Grade Architecture**:
   - **Security Headers**: Standard `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, and `Referrer-Policy`.
   - **CORS & Cookie Security**: Configured CORS middleware and production HTTPS cookie security flags.
   - **Health Monitoring**: Integrated `/api/health` monitoring endpoint.
   - **Serverless Resilience**: Read-only filesystem protection with `/tmp` and Data URL fallbacks for Vercel.

---

## 🚀 Quick Start Guide (Local Development)

### Run the Application
Open a terminal in the project directory and run:

```bash
python main.py
```

Or using `uvicorn`:
```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open your browser and navigate to:
```
http://127.0.0.1:8000
```

---

## ☁️ Deploying to Vercel (Production)

This project is configured out-of-the-box for **Vercel** serverless deployment with [vercel.json](./vercel.json) and [api/index.py](./api/index.py).

### Step 1: Initialize Git and Commit
```bash
git init
git add .
git commit -m "Initial commit for production"
```
*(The [.gitignore](./.gitignore) file automatically excludes `.env`, `node_modules`, `research_community.db`, and build caches so your credentials remain private.)*

### Step 2: Push to GitHub
Create a new repository on [GitHub](https://github.com/new) and push your code:
```bash
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy on Vercel
1. Log in to your [Vercel Dashboard](https://vercel.com/dashboard) and click **"Add New..." -> "Project"**.
2. Select your GitHub repository.
3. In **Environment Variables**, add the following keys from your `.env`:
   - `SUPABASE_URL`: `https://ccivcmvwhjireufzuvxs.supabase.co`
   - `SUPABASE_PUBLISHABLE_KEY`: `sb_publishable_JO3nsJXtytWuu1twvnpQGQ_LaCNyenW`
   - `SUPABASE_KEY`: `sb_publishable_JO3nsJXtytWuu1twvnpQGQ_LaCNyenW`
   - `SUPABASE_SECRET_KEY`: *(Your unmasked secret key from Supabase Dashboard)*
   - `JWT_SECRET`: *(A secure random string for JWT signing)*
   - `APP_ENV`: `production`
4. Click **Deploy**. Vercel will build the serverless Python environment and serve the application with worldwide CDN caching for static files.

---

## 🗄️ Setting Up Supabase Database

1. Open your Supabase project's SQL Editor:
   👉 **[https://supabase.com/dashboard/project/ccivcmvwhjireufzuvxs/sql/new](https://supabase.com/dashboard/project/ccivcmvwhjireufzuvxs/sql/new)**
2. Copy and execute the contents of [`schema.sql`](./schema.sql).
3. In **Storage**, create a public bucket named `avatars`.

---

## 📁 Project Structure

```
.
├── .gitignore            # Production Git exclusion rules
├── vercel.json           # Vercel serverless routing & build configuration
├── api/
│   └── index.py          # Vercel Serverless Function entrypoint
├── requirements.txt      # Python dependencies
├── package.json          # Node dependencies (@supabase/server)
├── schema.sql            # Supabase PostgreSQL schema with RLS & indexes
├── config.py             # Environment detection, Supabase & path settings
├── database.py           # Dual-backend storage engine (Supabase & SQLite fallback)
├── models.py             # Pydantic validation models
├── auth.py               # Bcrypt password hashing & JWT token management
├── main.py               # FastAPI server, security middleware & routes
├── static/
│   ├── css/
│   │   └── stylesheet.css   # Academic theme matching arnab9961.github.io
│   ├── js/
│   │   └── app.js           # Interactive client controller
│   ├── images/              # Avatars and favicon assets
│   └── uploads/avatars/     # Local uploaded profile photos
└── templates/
    ├── index.html           # Home page research feed
    └── profile.html         # Academic researcher profile portfolio
```
