const API_BASE = '/api';
const HYBRID_BASE = '/books';
const GOOGLE_BOOKS_BASE = '/api/books';

function mapHybridBook(book) {
  if (!book) return null;
  return {
    ...book,
    category_name: book.category || 'Uncategorized',
    book_type: book.book_type || 'hybrid',
    download_count: book.download_count || 0,
  };
}

function mapGoogleBook(book) {
  if (!book) return null;
  const rawAuthors = book.authors;
  const normalizedAuthors = Array.isArray(rawAuthors)
    ? rawAuthors
    : (rawAuthors ? String(rawAuthors).split(',').map((item) => item.trim()).filter(Boolean) : []);
  const volumeId = book.volumeId || book.volume_id || '';
  const pdfViewable = Boolean(book.pdfViewable ?? book.pdf_viewable ?? book.preview_available);
  const embeddable = Boolean(book.embeddable ?? pdfViewable);

  return {
    ...book,
    id: volumeId,
    volume_id: volumeId,
    volumeId,
    authors: normalizedAuthors,
    author: book.author || (normalizedAuthors.length ? normalizedAuthors.join(', ') : 'Unknown Author'),
    categories: Array.isArray(book.categories)
      ? book.categories
      : (book.categories ? String(book.categories).split(',').map((item) => item.trim()).filter(Boolean) : []),
    category_name: book.category_name || (Array.isArray(book.categories) && book.categories.length ? book.categories[0] : 'Google Books'),
    thumbnail: book.thumbnail || book.cover_image || '',
    cover_image: book.cover_image || book.thumbnail || '',
    preview_link: book.previewLink || book.preview_link || '',
    preview_available: pdfViewable,
    pdf_viewable: pdfViewable,
    embeddable,
    book_type: 'google_books',
    source: 'Google Books',
    download_count: 0,
  };
}

async function request(url, options = {}) {
  const res = await fetch(`${API_BASE}${url}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

async function archiveRequest(url, options = {}) {
  const res = await fetch(`${API_BASE}${url}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

export async function login(username, password) {
  return request('/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export async function register(userData) {
  return request('/register', {
    method: 'POST',
    body: JSON.stringify(userData),
  });
}

export async function logout() {
  return request('/logout', { method: 'POST' });
}

export async function getMe() {
  return request('/me');
}

export async function getStats() {
  const res = await fetch(`${HYBRID_BASE}/stats`, { credentials: 'include' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return {
    total_books: data.total_books || 0,
    total_downloads: 0,
    total_users: 0,
    total_verified: data.total_verified || 0,
    total_sources: data.total_sources || 0,
  };
}

export async function getArchiveStats() {
  const categories = await getArchiveCategories();
  const totalBooks = categories.reduce((sum, category) => sum + (category.book_count || 0), 0);
  return {
    total_books: totalBooks,
    total_verified: totalBooks,
    total_sources: categories.length,
  };
}

export async function getBooks(skip = 0, limit = 20, category = null) {
  let url = `${HYBRID_BASE}?skip=${skip}&limit=${limit}`;
  if (category) url += `&category=${encodeURIComponent(category)}`;
  const res = await fetch(url, { credentials: 'include' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return (data.items || []).map(mapHybridBook);
}

export async function getArchiveBooks(skip = 0, limit = 20, categoryId = null) {
  let url = `${API_BASE}/books?skip=${skip}&limit=${limit}`;
  if (categoryId) url += `&category_id=${encodeURIComponent(categoryId)}`;
  const res = await fetch(url, { credentials: 'include' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

export async function getBook(id) {
  const res = await fetch(`${HYBRID_BASE}/${id}`, { credentials: 'include' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return mapHybridBook(data);
}

export async function getArchiveBook(id) {
  return archiveRequest(`/books/${id}`);
}

export async function searchBooks(q, category = null) {
  let url = `${HYBRID_BASE}/search?q=${encodeURIComponent(q)}`;
  if (category) url += `&category=${encodeURIComponent(category)}`;
  const res = await fetch(url, { credentials: 'include' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return (data.items || []).map(mapHybridBook);
}

export async function searchGoogleBooks(q, field = 'all', maxResults = 12) {
  const params = new URLSearchParams({ q, field, source: 'google', max_results: String(maxResults), pdf_only: 'true' });
  const res = await fetch(`${GOOGLE_BOOKS_BASE}/search?${params.toString()}`, { credentials: 'include' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return (data.items || []).map(mapGoogleBook);
}

export async function searchGoogleBooksWithFilter(q, field = 'all', maxResults = 12, pdfOnly = true) {
  const params = new URLSearchParams({
    q,
    field,
    source: 'google',
    max_results: String(maxResults),
    pdf_only: String(Boolean(pdfOnly)),
  });
  const res = await fetch(`${GOOGLE_BOOKS_BASE}/search?${params.toString()}`, { credentials: 'include' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return (data.items || []).map(mapGoogleBook);
}

export async function getGoogleBook(volumeId) {
  const params = new URLSearchParams({ source: 'google' });
  const res = await fetch(`${GOOGLE_BOOKS_BASE}/${encodeURIComponent(volumeId)}?${params.toString()}`, { credentials: 'include' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return mapGoogleBook(data);
}

export async function getGoogleBookViewer(volumeId) {
  const params = new URLSearchParams({ source: 'google' });
  const res = await fetch(`${GOOGLE_BOOKS_BASE}/${encodeURIComponent(volumeId)}/viewer?${params.toString()}`, { credentials: 'include' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return mapGoogleBook(data);
}

export async function searchArchiveBooks(q, categoryId = null) {
  let url = `${API_BASE}/books/search?q=${encodeURIComponent(q)}`;
  if (categoryId) url += `&category_id=${encodeURIComponent(categoryId)}`;
  const res = await fetch(url, { credentials: 'include' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

export async function getCategories() {
  return getArchiveCategories();
}

export async function getArchiveCategories() {
  const res = await fetch(`${HYBRID_BASE}/categories`, { credentials: 'include' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return (data || []).map((cat) => ({
    id: cat.id ?? cat.slug ?? cat.name,
    name: cat.name,
    slug: cat.slug,
    description: cat.description || '',
    book_count: cat.book_count || 0,
  }));
}

export async function importFromArchive(archiveId, categoryId) {
  const body = new URLSearchParams({ category_id: String(categoryId) });
  const res = await fetch(`/archive/import/${encodeURIComponent(archiveId)}`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: body.toString(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Archive import failed');
  return data;
}

export async function triggerAutoImport(query, category, maxResultsPerSource = 8) {
  const res = await fetch(`${HYBRID_BASE}/auto-import`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, category, max_results_per_source: maxResultsPerSource }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Auto-import failed');
  return data;
}

export async function getAutoImportStatus(jobId) {
  const res = await fetch(`${HYBRID_BASE}/auto-import/${encodeURIComponent(jobId)}`, {
    credentials: 'include',
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Failed to get job status');
  return data;
}

export async function uploadBook(formData) {
  const res = await fetch(`${HYBRID_BASE}/upload`, {
    method: 'POST',
    credentials: 'include',
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Upload failed');
  return data;
}

export async function addDriveBook(formData) {
  throw new Error('Drive import is not enabled in the hybrid system.');
}

export async function deleteBook(id) {
  const res = await fetch(`${HYBRID_BASE}/${id}`, {
    method: 'DELETE',
    credentials: 'include',
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

export async function downloadBook(id) {
  window.open(`${HYBRID_BASE}/${id}/download`, '_blank', 'noopener');
  return { started: true };
}

export function getBookViewUrl(id) {
  return `${HYBRID_BASE}/${id}/view`;
}

export function getBookStreamUrl(id) {
  return `${HYBRID_BASE}/${id}/stream`;
}

export function getBookReadUrl(id) {
  return `/book/${id}/read`;
}

export function getArchiveBookViewUrl(id) {
  return `${API_BASE}/books/${id}/view`;
}

export function getArchiveBookDownloadUrl(id) {
  return `${API_BASE}/books/${id}/download`;
}
