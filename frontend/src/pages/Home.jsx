import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getBooks, getArchiveCategories, getStats } from '../api/client';
import { BookOpen, Users, Layers, ArrowRight, Shield, BarChart3, Brain } from 'lucide-react';
import BookCard from '../components/BookCard';

const CATEGORY_ICONS = {
  'cybersecurity': Shield,
  'data-science': BarChart3,
  'artificial-intelligence': Brain,
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

export default function Home() {
  const [stats, setStats] = useState({ total_books: 0, total_sources: 0 });
  const [recentBooks, setRecentBooks] = useState([]);
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    getStats().then(setStats).catch(() => {});
    getBooks(0, 8).then(setRecentBooks).catch(() => {});
    getArchiveCategories().then((cats) => setCategories(mergeCategoriesBySlug(cats))).catch(() => {});
  }, []);

  return (
    <div className="home-page">
      {/* Stats Row */}
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

      {/* Categories */}
      <div className="section">
        <div className="section-head">
          <h2>Browse Categories</h2>
          <Link to="/library" className="view-all-link">View All <ArrowRight size={14} /></Link>
        </div>
        <div className="categories-grid">
          {categories.map((cat) => {
            const Icon = CATEGORY_ICONS[cat.slug] || BookOpen;
            return (
              <Link key={cat.id} to={`/library/category/${cat.slug}`} className="category-card">
                <div className="category-icon"><Icon size={22} /></div>
                <div className="category-name">{cat.name}</div>
                <div className="category-count">{cat.book_count} books</div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Recent Books */}
      <div className="section">
        <div className="section-head">
          <h2>Recently Added</h2>
          <Link to="/library" className="view-all-link">View All <ArrowRight size={14} /></Link>
        </div>
        {recentBooks.length > 0 ? (
          <div className="book-grid">
            {recentBooks.map((book) => <BookCard key={book.id} book={book} />)}
          </div>
        ) : (
          <div className="empty-state">
            <BookOpen size={48} strokeWidth={1} />
            <h3>No books yet</h3>
            <p>Import books from Internet Archive to get started.</p>
          </div>
        )}
      </div>
    </div>
  );
}
