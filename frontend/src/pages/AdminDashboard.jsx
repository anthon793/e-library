import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getStats, getBooks, getArchiveCategories, deleteBook as deleteBookApi } from '../api/client';
import { BookOpen, Users, Layers, Trash2, Eye, Shield, BarChart3, Brain, Network, Code } from 'lucide-react';
import Modal from '../components/Modal';

const CATEGORY_ICONS = {
  'cybersecurity': Shield,
  'data-science': BarChart3,
  'artificial-intelligence': Brain,
  'information-systems': Network,
  'computer-science': Code,
};

function mergeCategoriesBySlug(items) {
  const merged = new Map();
  for (const cat of items || []) {
    const slug = String(cat?.slug || '').trim();
    if (!slug) continue;

    const existing = merged.get(slug);
    if (!existing) {
      merged.set(slug, {
        ...cat,
        book_count: Number(cat.book_count || 0),
      });
      continue;
    }

    existing.book_count += Number(cat.book_count || 0);
    if (String(cat.name || '').length > String(existing.name || '').length) {
      existing.name = cat.name;
    }
  }
  return Array.from(merged.values());
}

export default function AdminDashboard() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({ total_books: 0, total_sources: 0 });
  const [books, setBooks] = useState([]);
  const [categories, setCategories] = useState([]);
  const [deleteModal, setDeleteModal] = useState({ isOpen: false, bookId: null, bookTitle: '' });
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (loading) {
      return;
    }
    if (!user || user.role !== 'admin') {
      navigate('/login');
      return;
    }
    getStats().then(setStats).catch(() => {});
    getBooks(0, 50).then(setBooks).catch(() => {});
    getArchiveCategories().then((cats) => setCategories(mergeCategoriesBySlug(cats))).catch(() => {});
  }, [user, loading, navigate]);

  if (loading) {
    return <div className="page-header"><h1>Loading...</h1></div>;
  }

  const handleDelete = (id) => {
    const book = books.find((b) => b.id === id);
    setDeleteModal({
      isOpen: true,
      bookId: id,
      bookTitle: book?.title || 'Unknown',
    });
  };

  const confirmDelete = async () => {
    const { bookId } = deleteModal;
    setDeleting(true);
    try {
      await deleteBookApi(bookId);
      setBooks((prev) => prev.filter((b) => b.id !== bookId));
      setStats((prev) => ({ ...prev, total_books: prev.total_books - 1 }));
      setDeleteModal({ isOpen: false, bookId: null, bookTitle: '' });
    } catch (err) {
      alert(err.message);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Admin Dashboard</h1>
        <p className="page-subtitle">Overview of library activity and statistics</p>
      </div>

      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-icon icon-primary"><BookOpen size={20} /></div>
          <div>
            <div className="stat-value">{stats.total_books}</div>
            <div className="stat-label">Total Books</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon icon-gold"><Users size={20} /></div>
          <div>
            <div className="stat-value">{stats.total_sources}</div>
            <div className="stat-label">Sources</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon icon-emerald"><Layers size={20} /></div>
          <div>
            <div className="stat-value">{categories.length}</div>
            <div className="stat-label">Categories</div>
          </div>
        </div>
      </div>

      {/* Category breakdown */}
      <div className="section">
        <h2>Books by Category</h2>
        <div className="categories-grid" style={{ marginTop: 16 }}>
          {categories.map((cat) => {
            const Icon = CATEGORY_ICONS[cat.slug] || BookOpen;
            return (
              <div key={cat.id} className="category-card" style={{ cursor: 'default' }}>
                <div className="category-icon"><Icon size={22} /></div>
                <div className="category-name">{cat.name}</div>
                <div className="category-count-lg">{cat.book_count}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Books Table */}
      <div className="section">
        <div className="section-head">
          <h2>All Books</h2>
          <Link to="/upload" className="btn btn-primary btn-sm">+ Add Book</Link>
        </div>
        {books.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Author</th>
                  <th>Category</th>
                  <th>Type</th>
                  <th>Downloads</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {books.map((book) => (
                  <tr key={book.id}>
                    <td><Link to={`/book/${book.id}`} className="table-link">{book.title?.substring(0, 50)}{book.title?.length > 50 ? '...' : ''}</Link></td>
                    <td>{book.author?.substring(0, 30)}</td>
                    <td>{book.category_name || '—'}</td>
                    <td><span className={`type-badge type-${book.book_type}`}>{book.book_type}</span></td>
                    <td>{book.download_count}</td>
                    <td>
                      <div className="table-actions">
                        <Link to={`/book/${book.id}`} className="btn btn-secondary btn-xs"><Eye size={13} /></Link>
                        <button className="btn btn-danger btn-xs" onClick={() => handleDelete(book.id)}><Trash2 size={13} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state"><h3>No books</h3></div>
        )}
      </div>

      <Modal
        isOpen={deleteModal.isOpen}
        onClose={() => setDeleteModal({ isOpen: false, bookId: null, bookTitle: '' })}
        title="Delete Book"
        isDanger={true}
        isLoading={deleting}
        confirmText="Delete"
        onConfirm={confirmDelete}
      >
        <p>Are you sure you want to delete this book?</p>
        <p><strong>{deleteModal.bookTitle}</strong></p>
        <p style={{ marginTop: '16px', fontSize: '0.9rem', color: 'var(--gray-500)' }}>This action cannot be undone.</p>
      </Modal>
    </div>
  );
}
