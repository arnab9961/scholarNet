/**
 * ScholarNet - Academic Research & Publication Community
 * Frontend Client Controller
 */

let currentUser = null;
let currentActiveTag = 'all';

// ==============================================================================
// INITIALIZATION
// ==============================================================================
document.addEventListener('DOMContentLoaded', async () => {
  await checkAuthStatus();
  initEventListeners();
});

// ==============================================================================
// AUTH STATUS
// ==============================================================================
async function checkAuthStatus() {
  try {
    const res = await fetch('/api/auth/me');
    if (res.ok) {
      currentUser = await res.json();
      renderAuthNav(true);
    } else {
      currentUser = null;
      renderAuthNav(false);
    }
  } catch (err) {
    currentUser = null;
    renderAuthNav(false);
  }
}

function renderAuthNav(isLoggedIn) {
  const authNav = document.getElementById('auth-nav-container');
  if (!authNav) return;

  if (isLoggedIn && currentUser) {
    authNav.innerHTML = `
      <a href="/profile/${currentUser.id}" class="nav-profile-link" title="View Academic Profile">
        <img src="${currentUser.avatar_url || '/static/images/default-avatar.png'}" class="nav-avatar" alt="Profile">
        <span>${currentUser.full_name.split(' ')[0]}</span>
      </a>
      <button onclick="openNewPostModal()" class="nav-btn">+ New Publication</button>
      <button onclick="handleLogout()" class="action-pill" style="color:#777;">Sign Out</button>
    `;
  } else {
    authNav.innerHTML = `
      <button onclick="openAuthModal('login')" class="action-pill" style="font-weight:700;">Sign In</button>
      <button onclick="openAuthModal('register')" class="nav-btn">Register</button>
    `;
  }
}

// ==============================================================================
// EVENT LISTENERS & FILTERING
// ==============================================================================
function initEventListeners() {
  // Search input
  const searchInput = document.getElementById('feed-search-input');
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        loadPosts(e.target.value.trim(), currentActiveTag);
      }, 300);
    });
  }

  // Tag filter pills
  document.querySelectorAll('.tag-pill').forEach((pill) => {
    pill.addEventListener('click', (e) => {
      document.querySelectorAll('.tag-pill').forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      currentActiveTag = pill.getAttribute('data-tag') || 'all';
      const searchVal = document.getElementById('feed-search-input')?.value.trim() || '';
      loadPosts(searchVal, currentActiveTag);
    });
  });
}

// ==============================================================================
// POSTS FEED LOADER
// ==============================================================================
async function loadPosts(search = '', tag = 'all') {
  const feedContainer = document.getElementById('posts-feed-container');
  if (!feedContainer) return;

  try {
    let url = `/api/posts?tag=${encodeURIComponent(tag)}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;

    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch posts');
    const posts = await res.json();

    if (posts.length === 0) {
      feedContainer.innerHTML = `
        <div style="padding: 40px 20px; text-align: center; color: #666; background: #fbfbfc; border: 1px dashed #cbd5e1; border-radius: 6px;">
          <p style="font-size: 16px; margin-bottom: 8px;"><strong>No publications found matching criteria.</strong></p>
          <p style="font-size: 14px;">Try clearing filters or be the first to publish a paper update!</p>
        </div>
      `;
      return;
    }

    feedContainer.innerHTML = posts.map((post) => renderPostCard(post)).join('');
  } catch (err) {
    console.error(err);
    feedContainer.innerHTML = `<p style="color: red; padding: 20px;">Error loading research feed. Please retry.</p>`;
  }
}

// ==============================================================================
// POST CARD RENDERING (Matching arnab9961.github.io academic publication item)
// ==============================================================================
function renderPostCard(post) {
  const tagsHtml = (post.tags || '')
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean)
    .map((t, idx) => {
      const badgeClasses = ['label-pps', 'label-lab', 'label-lecture', 'label-function'];
      const badgeClass = badgeClasses[idx % badgeClasses.length];
      return `<span class="label ${badgeClass}">${t}</span>`;
    })
    .join(' ');

  const likedClass = post.is_liked_by_user ? 'active' : '';

  return `
    <div class="post-card" id="post-${post.id}">
      <div class="post-row">
        <!-- Author Avatar Thumbnail -->
        <div class="post-author-thumbnail">
          <a href="/profile/${post.user_id}" class="hoverZoomLink" title="View ${post.author_name}'s profile">
            <img src="${post.author_avatar || '/static/images/default-avatar.png'}" alt="${post.author_name}">
          </a>
        </div>

        <!-- Post Content Area -->
        <div class="post-content-area">
          <div class="post-title-line">
            <a href="${post.paper_link || `/profile/${post.user_id}`}" target="_blank" class="post-title-link">
              <papertitle>${escapeHtml(post.title)}</papertitle>
            </a>
          </div>

          <div class="post-authors-line">
            <a href="/profile/${post.user_id}" class="post-author-badge">${escapeHtml(post.author_name)}</a>
            <span style="color:#666;"> &middot; ${escapeHtml(post.author_university)}</span>
          </div>

          ${
            post.venue
              ? `<div class="post-venue-line">
                  <span>${escapeHtml(post.venue)}</span>${post.year ? `, ${post.year}` : ''}
                </div>`
              : ''
          }

          <div class="post-abstract">
            ${escapeHtml(post.abstract)}
          </div>

          ${tagsHtml ? `<div class="post-tags-line">${tagsHtml}</div>` : ''}

          <!-- Action Links & Community Engagement Toolbar -->
          <div class="post-action-links">
            ${
              post.paper_link
                ? `<a href="${post.paper_link}" target="_blank" class="action-pill">[Paper / PDF]</a>`
                : ''
            }
            ${
              post.code_link
                ? `<a href="${post.code_link}" target="_blank" class="action-pill">[Code / GitHub]</a>`
                : ''
            }
            ${
              post.project_link
                ? `<a href="${post.project_link}" target="_blank" class="action-pill">[Project]</a>`
                : ''
            }
            ${
              post.bibtex
                ? `<button onclick="toggleBibtex('${post.id}')" class="action-pill">[BibTeX]</button>`
                : ''
            }
            
            <button onclick="handleLike('${post.id}')" class="action-pill ${likedClass}" id="like-btn-${post.id}">
              <span id="like-heart-${post.id}">${post.is_liked_by_user ? '★' : '☆'}</span>
              <span id="like-count-${post.id}">${post.likes_count}</span> Upvotes
            </button>

            <button onclick="toggleComments('${post.id}')" class="action-pill">
              💬 <span id="comments-count-${post.id}">${post.comments ? post.comments.length : 0}</span> Comments
            </button>

            <button onclick="openShareModal('${post.id}', '${escapeAttr(post.title)}', '${escapeAttr(post.bibtex || '')}')" class="action-pill">
              🔁 <span id="share-count-${post.id}">${post.shares_count || 0}</span> Share
            </button>
          </div>

          <!-- BibTeX Accordion -->
          ${
            post.bibtex
              ? `
            <div class="bibtex-box" id="bibtex-${post.id}">
              <button class="copy-bibtex-btn" onclick="copyBibtex('${post.id}')">Copy</button>
              <code id="bibtex-code-${post.id}">${escapeHtml(post.bibtex)}</code>
            </div>`
              : ''
          }

          <!-- Comments Drawer -->
          <div class="comments-container" id="comments-${post.id}">
            <div class="comments-header">Peer Feedback & Research Discussion</div>
            <div class="comment-list" id="comment-list-${post.id}">
              ${renderCommentsList(post.comments || [])}
            </div>

            <!-- Comment Input Box -->
            <div class="comment-input-area">
              <input type="text" id="comment-input-${post.id}" class="comment-input" placeholder="Write academic feedback, inquiry, or comment..." onkeydown="if(event.key==='Enter') submitComment('${post.id}')">
              <button onclick="submitComment('${post.id}')" class="comment-submit-btn">Comment</button>
            </div>
          </div>

        </div>
      </div>
    </div>
  `;
}

function renderCommentsList(comments) {
  if (!comments || comments.length === 0) {
    return `<div style="font-size: 13px; color: #777; font-style: italic;">No comments yet. Start the academic discussion!</div>`;
  }
  return comments
    .map(
      (c) => `
    <div class="comment-item">
      <img src="${c.author_avatar || '/static/images/default-avatar.png'}" class="comment-avatar" alt="User">
      <div class="comment-body">
        <div class="comment-meta">
          <a href="/profile/${c.user_id}" class="comment-author">${escapeHtml(c.author_name)}</a>
          <span> &middot; ${escapeHtml(c.author_university || '')}</span>
          <span style="color:#888;"> &middot; ${formatDate(c.created_at)}</span>
        </div>
        <div class="comment-text">${escapeHtml(c.content)}</div>
      </div>
    </div>
  `
    )
    .join('');
}

// ==============================================================================
// LIKES & ENGAGEMENT
// ==============================================================================
async function handleLike(postId) {
  if (!currentUser) {
    openAuthModal('login');
    showToast('Please sign in to upvote publications', 'info');
    return;
  }

  try {
    const res = await fetch(`/api/posts/${postId}/like`, { method: 'POST' });
    if (!res.ok) throw new Error('Like failed');
    const data = await res.json();

    const countElem = document.getElementById(`like-count-${postId}`);
    const heartElem = document.getElementById(`like-heart-${postId}`);
    const btnElem = document.getElementById(`like-btn-${postId}`);

    if (countElem) countElem.innerText = data.likes_count;
    if (heartElem) heartElem.innerText = data.liked ? '★' : '☆';
    if (btnElem) {
      if (data.liked) btnElem.classList.add('active');
      else btnElem.classList.remove('active');
    }
  } catch (err) {
    showToast('Could not record vote. Please try again.', 'error');
  }
}

// ==============================================================================
// COMMENTS
// ==============================================================================
function toggleComments(postId) {
  const container = document.getElementById(`comments-${postId}`);
  if (container) {
    container.style.display = container.style.display === 'block' ? 'none' : 'block';
  }
}

async function submitComment(postId) {
  if (!currentUser) {
    openAuthModal('login');
    showToast('Please sign in to comment', 'info');
    return;
  }

  const inputElem = document.getElementById(`comment-input-${postId}`);
  const content = inputElem?.value.trim();
  if (!content) return;

  try {
    const res = await fetch(`/api/posts/${postId}/comment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });

    if (!res.ok) throw new Error('Comment submission failed');
    const newComment = await res.json();

    // Clear input
    inputElem.value = '';

    // Append to list
    const listElem = document.getElementById(`comment-list-${postId}`);
    if (listElem) {
      const commentHtml = `
        <div class="comment-item">
          <img src="${newComment.author_avatar || '/static/images/default-avatar.png'}" class="comment-avatar" alt="User">
          <div class="comment-body">
            <div class="comment-meta">
              <a href="/profile/${newComment.user_id}" class="comment-author">${escapeHtml(newComment.author_name)}</a>
              <span> &middot; ${escapeHtml(newComment.author_university || '')}</span>
              <span style="color:#888;"> &middot; Just now</span>
            </div>
            <div class="comment-text">${escapeHtml(newComment.content)}</div>
          </div>
        </div>
      `;
      // If was empty
      if (listElem.innerHTML.includes('No comments yet')) {
        listElem.innerHTML = commentHtml;
      } else {
        listElem.innerHTML += commentHtml;
      }
    }

    // Update count
    const countElem = document.getElementById(`comments-count-${postId}`);
    if (countElem) {
      countElem.innerText = parseInt(countElem.innerText || '0', 10) + 1;
    }

    showToast('Comment posted successfully!');
  } catch (err) {
    showToast('Failed to post comment.', 'error');
  }
}

// ==============================================================================
// SHARE MODAL & FUNCTIONALITY
// ==============================================================================
let activeSharePostId = null;

function openShareModal(postId, title, bibtex) {
  activeSharePostId = postId;
  const modal = document.getElementById('share-modal');
  const linkInput = document.getElementById('share-link-input');
  const titleDisplay = document.getElementById('share-post-title');
  const bibtexArea = document.getElementById('share-bibtex-area');

  const shareUrl = `${window.location.origin}/#post-${postId}`;
  if (linkInput) linkInput.value = shareUrl;
  if (titleDisplay) titleDisplay.innerText = title;
  if (bibtexArea) bibtexArea.value = bibtex || '';

  // Increment share count on server
  fetch(`/api/posts/${postId}/share`, { method: 'POST' })
    .then((r) => r.json())
    .then((data) => {
      const countElem = document.getElementById(`share-count-${postId}`);
      if (countElem && data.shares_count) countElem.innerText = data.shares_count;
    })
    .catch(() => {});

  if (modal) modal.style.display = 'flex';
}

function closeShareModal() {
  const modal = document.getElementById('share-modal');
  if (modal) modal.style.display = 'none';
}

function copyShareLink() {
  const linkInput = document.getElementById('share-link-input');
  if (linkInput) {
    navigator.clipboard.writeText(linkInput.value);
    showToast('Publication link copied to clipboard!');
  }
}

function copyShareBibtex() {
  const bibtexArea = document.getElementById('share-bibtex-area');
  if (bibtexArea && bibtexArea.value) {
    navigator.clipboard.writeText(bibtexArea.value);
    showToast('BibTeX citation copied to clipboard!');
  }
}

function shareOnTwitter() {
  const title = document.getElementById('share-post-title')?.innerText || '';
  const url = document.getElementById('share-link-input')?.value || '';
  const tweetText = encodeURIComponent(`Read this research on ScholarNet: "${title}" ${url}`);
  window.open(`https://twitter.com/intent/tweet?text=${tweetText}`, '_blank');
}

function shareOnLinkedIn() {
  const url = encodeURIComponent(document.getElementById('share-link-input')?.value || '');
  window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${url}`, '_blank');
}

// ==============================================================================
// BIBTEX TOGGLE
// ==============================================================================
function toggleBibtex(postId) {
  const box = document.getElementById(`bibtex-${postId}`);
  if (box) {
    box.style.display = box.style.display === 'block' ? 'none' : 'block';
  }
}

function copyBibtex(postId) {
  const code = document.getElementById(`bibtex-code-${postId}`)?.innerText;
  if (code) {
    navigator.clipboard.writeText(code);
    showToast('BibTeX copied to clipboard!');
  }
}

// ==============================================================================
// NEW POST MODAL
// ==============================================================================
function openNewPostModal() {
  if (!currentUser) {
    openAuthModal('login');
    showToast('Please sign in to publish a paper', 'info');
    return;
  }
  const modal = document.getElementById('new-post-modal');
  if (modal) modal.style.display = 'flex';
}

function closeNewPostModal() {
  const modal = document.getElementById('new-post-modal');
  if (modal) modal.style.display = 'none';
}

async function handleCreatePost(event) {
  event.preventDefault();
  const form = event.target;

  const payload = {
    title: form.title.value.trim(),
    venue: form.venue.value.trim(),
    year: parseInt(form.year.value, 10) || new Date().getFullYear(),
    tags: form.tags.value.trim(),
    abstract: form.abstract.value.trim(),
    paper_link: form.paper_link.value.trim(),
    code_link: form.code_link.value.trim(),
    project_link: form.project_link.value.trim(),
    bibtex: form.bibtex.value.trim(),
  };

  try {
    const res = await fetch('/api/posts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create post');
    }

    form.reset();
    closeNewPostModal();
    showToast('Research publication posted successfully!');
    await loadPosts();
  } catch (err) {
    showToast(err.message || 'Error publishing post', 'error');
  }
}

// Auto-generate BibTeX in New Post Modal
function autoGenerateBibtex() {
  const form = document.getElementById('new-post-form');
  if (!form) return;

  const title = form.title.value.trim() || 'Research Title';
  const author = currentUser ? currentUser.full_name : 'Author Name';
  const venue = form.venue.value.trim() || 'arXiv Preprint';
  const year = form.year.value.trim() || new Date().getFullYear();
  const citeKey = `${author.split(' ').pop().toLowerCase()}${year}${title.split(' ')[0].toLowerCase()}`;

  form.bibtex.value = `@article{${citeKey},
  title={${title}},
  author={${author}},
  journal={${venue}},
  year={${year}}
}`;
  showToast('BibTeX generated!');
}

// ==============================================================================
// AUTHENTICATION MODAL (Sign In & Registration)
// ==============================================================================
function openAuthModal(tab = 'login') {
  const modal = document.getElementById('auth-modal');
  if (modal) modal.style.display = 'flex';
  switchAuthTab(tab);
}

function closeAuthModal() {
  const modal = document.getElementById('auth-modal');
  if (modal) modal.style.display = 'none';
}

function switchAuthTab(tab) {
  const loginForm = document.getElementById('login-form-container');
  const registerForm = document.getElementById('register-form-container');
  const loginTab = document.getElementById('auth-tab-login');
  const registerTab = document.getElementById('auth-tab-register');

  if (tab === 'login') {
    loginForm.style.display = 'block';
    registerForm.style.display = 'none';
    loginTab.style.borderBottom = '2px solid var(--primary-maroon)';
    loginTab.style.fontWeight = 'bold';
    registerTab.style.borderBottom = 'none';
    registerTab.style.fontWeight = 'normal';
  } else {
    loginForm.style.display = 'none';
    registerForm.style.display = 'block';
    registerTab.style.borderBottom = '2px solid var(--primary-maroon)';
    registerTab.style.fontWeight = 'bold';
    loginTab.style.borderBottom = 'none';
    loginTab.style.fontWeight = 'normal';
  }
}

async function handleLogin(event) {
  event.preventDefault();
  const form = event.target;
  const email = form.email.value.trim();
  const password = form.password.value;

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Login failed');
    }

    const data = await res.json();
    currentUser = data.user;
    renderAuthNav(true);
    closeAuthModal();
    showToast(`Welcome back, ${currentUser.full_name}!`);
    await loadPosts();
  } catch (err) {
    showToast(err.message || 'Login failed', 'error');
  }
}

async function handleRegister(event) {
  event.preventDefault();
  const form = event.target;

  const payload = {
    full_name: form.full_name.value.trim(),
    university: form.university.value.trim(),
    email: form.email.value.trim(),
    password: form.password.value,
  };

  try {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Registration failed');
    }

    const data = await res.json();
    currentUser = data.user;
    renderAuthNav(true);
    closeAuthModal();
    showToast(`Account created! Welcome to ScholarNet, ${currentUser.full_name}!`);
    await loadPosts();
  } catch (err) {
    showToast(err.message || 'Registration failed', 'error');
  }
}

async function handleLogout() {
  try {
    await fetch('/api/auth/logout', { method: 'POST' });
    currentUser = null;
    renderAuthNav(false);
    showToast('You have been signed out.');
    window.location.href = '/';
  } catch (err) {
    console.error(err);
  }
}

// ==============================================================================
// PROFILE EDITING & AVATAR UPLOAD
// ==============================================================================
function openEditProfileModal() {
  if (!currentUser) return;
  const modal = document.getElementById('edit-profile-modal');
  const form = document.getElementById('edit-profile-form');

  if (form) {
    form.full_name.value = currentUser.full_name || '';
    form.university.value = currentUser.university || '';
    form.bio.value = currentUser.bio || '';
    form.research_interests.value = currentUser.research_interests || '';
    form.cv_link.value = currentUser.cv_link || '';
    form.github_link.value = currentUser.github_link || '';
    form.scholar_link.value = currentUser.scholar_link || '';
    form.linkedin_link.value = currentUser.linkedin_link || '';
    form.researchgate_link.value = currentUser.researchgate_link || '';

    const preview = document.getElementById('edit-avatar-preview');
    if (preview) preview.src = currentUser.avatar_url || '/static/images/default-avatar.png';
  }

  if (modal) modal.style.display = 'flex';
}

function closeEditProfileModal() {
  const modal = document.getElementById('edit-profile-modal');
  if (modal) modal.style.display = 'none';
}

async function handleProfileUpdate(event) {
  event.preventDefault();
  const form = event.target;

  const payload = {
    full_name: form.full_name.value.trim(),
    university: form.university.value.trim(),
    bio: form.bio.value.trim(),
    research_interests: form.research_interests.value.trim(),
    cv_link: form.cv_link.value.trim(),
    github_link: form.github_link.value.trim(),
    scholar_link: form.scholar_link.value.trim(),
    linkedin_link: form.linkedin_link.value.trim(),
    researchgate_link: form.researchgate_link.value.trim(),
  };

  try {
    const res = await fetch('/api/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Profile update failed');
    }

    currentUser = await res.json();
    closeEditProfileModal();
    showToast('Academic profile updated successfully!');
    // If on profile page, reload to reflect updates
    if (window.location.pathname.startsWith('/profile/')) {
      window.location.reload();
    } else {
      renderAuthNav(true);
      await loadPosts();
    }
  } catch (err) {
    showToast(err.message || 'Error updating profile', 'error');
  }
}

async function handleAvatarUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/profile/upload-avatar', {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Avatar upload failed');
    }

    const data = await res.json();
    if (currentUser) currentUser.avatar_url = data.avatar_url;

    // Update preview
    const preview = document.getElementById('edit-avatar-preview');
    if (preview) preview.src = data.avatar_url;

    const navAvatar = document.querySelector('.nav-avatar');
    if (navAvatar) navAvatar.src = data.avatar_url;

    showToast('Profile photo uploaded successfully!');
  } catch (err) {
    showToast(err.message || 'Error uploading photo', 'error');
  }
}

// ==============================================================================
// HELPERS
// ==============================================================================
function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = 'toast show';
  toast.innerText = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function escapeAttr(str) {
  if (!str) return '';
  return String(str).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function formatDate(isoStr) {
  if (!isoStr) return '';
  try {
    const date = new Date(isoStr);
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return isoStr;
  }
}
