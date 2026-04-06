// ================================================================
// Academic E-Library — Client-Side JavaScript
// ================================================================

// ---------- Toast Notifications ----------
function showToast(message, type = 'success') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span> ${message}`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ---------- Auth Functions ----------
async function handleLogin(event) {
  event.preventDefault();
  const form = event.target;
  const username = form.querySelector('#username').value;
  const password = form.querySelector('#password').value;

  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    const data = await response.json();
    if (response.ok) {
      showToast('Login successful! Redirecting...', 'success');
      setTimeout(() => window.location.href = '/library', 800);
    } else {
      showToast(data.detail || 'Login failed', 'error');
    }
  } catch (err) {
    showToast('Connection error. Please try again.', 'error');
  }
}

async function handleRegister(event) {
  event.preventDefault();
  const form = event.target;
  const username = form.querySelector('#username').value;
  const email = form.querySelector('#email').value;
  const full_name = form.querySelector('#full_name').value;
  const password = form.querySelector('#password').value;
  const confirm = form.querySelector('#confirm_password').value;
  const roleEl = document.querySelector('.role-option.selected');
  const role = roleEl ? roleEl.dataset.role : 'student';

  if (password !== confirm) {
    showToast('Passwords do not match', 'error');
    return;
  }

  try {
    const response = await fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, full_name, password, role }),
    });

    const data = await response.json();
    if (response.ok) {
      showToast('Registration successful! Please log in.', 'success');
      setTimeout(() => window.location.href = '/login', 1000);
    } else {
      showToast(data.detail || 'Registration failed', 'error');
    }
  } catch (err) {
    showToast('Connection error. Please try again.', 'error');
  }
}

async function handleLogout() {
  await fetch('/api/logout', { method: 'POST' });
  window.location.href = '/';
}

// ---------- Role Selection ----------
function selectRole(element) {
  document.querySelectorAll('.role-option').forEach(el => el.classList.remove('selected'));
  element.classList.add('selected');
}

// ---------- Upload Functions ----------
function switchUploadTab(tabName) {
  document.querySelectorAll('.upload-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.upload-form-panel').forEach(p => p.style.display = 'none');

  event.target.classList.add('active');
  const panel = document.getElementById(`panel-${tabName}`);
  if (panel) panel.style.display = 'block';
}

function initFileUpload() {
  const zone = document.querySelector('.file-upload-zone');
  const input = document.getElementById('pdf-file');
  if (!zone || !input) return;

  zone.addEventListener('click', () => input.click());

  zone.addEventListener('dragover', (e) => {
    e.preventDefault();
    zone.classList.add('dragover');
  });

  zone.addEventListener('dragleave', () => {
    zone.classList.remove('dragover');
  });

  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
      input.files = e.dataTransfer.files;
      updateFileName(input.files[0].name);
    }
  });

  input.addEventListener('change', () => {
    if (input.files.length) {
      updateFileName(input.files[0].name);
    }
  });
}

function updateFileName(name) {
  const zone = document.querySelector('.file-upload-zone');
  if (zone) {
    zone.querySelector('p').innerHTML = `<strong>📎 ${name}</strong> — Ready to upload`;
  }
}

async function handleUploadBook(event) {
  event.preventDefault();
  const form = event.target;
  const formData = new FormData(form);

  try {
    showToast('Uploading book...', 'info');
    const response = await fetch('/api/books/upload', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();
    if (response.ok) {
      showToast('Book uploaded successfully!', 'success');
      setTimeout(() => window.location.href = '/library', 1000);
    } else {
      showToast(data.detail || 'Upload failed', 'error');
    }
  } catch (err) {
    showToast('Upload failed. Please try again.', 'error');
  }
}

async function handleAddDriveBook(event) {
  event.preventDefault();
  const form = event.target;
  const formData = new FormData(form);

  try {
    const response = await fetch('/api/books/add-drive', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();
    if (response.ok) {
      showToast('Drive book added successfully!', 'success');
      setTimeout(() => window.location.href = '/library', 1000);
    } else {
      showToast(data.detail || 'Failed to add book', 'error');
    }
  } catch (err) {
    showToast('Error adding book. Please try again.', 'error');
  }
}

// ---------- External API Search ----------
async function searchOpenLibrary(event) {
  event.preventDefault();
  const query = document.getElementById('import-search-input').value;
  if (!query.trim()) return;

  const resultsDiv = document.getElementById('import-results');
  resultsDiv.innerHTML = '<div style="text-align:center;padding:40px;"><div class="spinner"></div><p style="margin-top:16px;color:var(--gray-500);">Searching Open Library...</p></div>';

  try {
    const response = await fetch(`/api/openlibrary/search?q=${encodeURIComponent(query)}`);
    const results = await response.json();

    if (results.length === 0) {
      resultsDiv.innerHTML = '<div class="empty-state"><div class="empty-icon">🔍</div><h3>No books found</h3><p>Try a different search term.</p></div>';
      return;
    }

    resultsDiv.innerHTML = results.map(book => `
      <div class="import-result-card">
        <div class="result-cover">
          ${book.cover_image
            ? `<img src="${book.cover_image}" alt="${book.title}" loading="lazy" decoding="async" onerror="this.parentElement.innerHTML='<div style=\\'display:flex;align-items:center;justify-content:center;height:100%;font-size:2rem;\\'>📚</div>'">`
            : '<div style="display:flex;align-items:center;justify-content:center;height:100%;font-size:2rem;">📚</div>'
          }
        </div>
        <div class="result-info">
          <h3>${book.title}</h3>
          <p class="result-author">by ${book.author}</p>
          <p style="font-size:0.82rem;color:var(--gray-400);">Source: Open Library</p>
        </div>
        <div class="result-actions">
          <button class="btn btn-primary btn-sm" onclick='importBook(${JSON.stringify(book).replace(/'/g, "&#39;")})'>
            + Import
          </button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    resultsDiv.innerHTML = '<div class="empty-state"><div class="empty-icon">⚠️</div><h3>Search failed</h3><p>Please check your connection and try again.</p></div>';
  }
}

async function importBook(book) {
  // Show category selection modal
  const categorySelect = document.getElementById('import-category');
  const categoryId = categorySelect ? categorySelect.value : '';

  if (!categoryId) {
    showToast('Select a category before importing a book.', 'error');
    return;
  }

  const formData = new FormData();
  formData.append('api_id', book.api_id);
  formData.append('title', book.title);
  formData.append('author', book.author);
  formData.append('description', book.description || '');
  formData.append('cover_image', book.cover_image || '');
  formData.append('view_link', book.view_link || '');
  if (categoryId) formData.append('category_id', categoryId);

  try {
    const response = await fetch('/api/import/openlibrary', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();
    if (response.ok) {
      showToast(`"${book.title}" imported successfully!`, 'success');
    } else {
      showToast(data.detail || 'Import failed', 'error');
    }
  } catch (err) {
    showToast('Import failed. Please try again.', 'error');
  }
}

// ---------- Book Actions ----------
async function deleteBook(bookId) {
  if (!confirm('Are you sure you want to delete this book?')) return;

  try {
    const response = await fetch(`/api/books/${bookId}`, { method: 'DELETE' });
    const data = await response.json();
    if (response.ok) {
      showToast('Book deleted successfully', 'success');
      setTimeout(() => window.location.reload(), 800);
    } else {
      showToast(data.detail || 'Delete failed', 'error');
    }
  } catch (err) {
    showToast('Error deleting book', 'error');
  }
}

async function downloadBook(bookId) {
  try {
    const response = await fetch(`/api/books/${bookId}/download`);
    if (response.headers.get('content-type')?.includes('application/pdf')) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'book.pdf';
      a.click();
      window.URL.revokeObjectURL(url);
      showToast('Download started!', 'success');
    } else {
      const data = await response.json();
      if (data.redirect) {
        window.open(data.redirect, '_blank');
      }
    }
  } catch (err) {
    showToast('Download failed', 'error');
  }
}

// ---------- Search ----------
function handleSearch(event) {
  if (event.key === 'Enter') {
    const query = event.target.value.trim();
    if (query) {
      window.location.href = `/library/search?q=${encodeURIComponent(query)}`;
    }
  }
}

// ---------- Mobile Menu ----------
function toggleMobileMenu() {
  const links = document.querySelector('.navbar-links');
  if (links) {
    links.style.display = links.style.display === 'flex' ? 'none' : 'flex';
    links.style.position = 'absolute';
    links.style.top = '68px';
    links.style.left = '0';
    links.style.right = '0';
    links.style.background = 'var(--primary)';
    links.style.flexDirection = 'column';
    links.style.padding = '16px';
    links.style.borderTop = '1px solid rgba(255,255,255,0.1)';
  }
}

// ---------- Init ----------
document.addEventListener('DOMContentLoaded', () => {
  initFileUpload();
});
