import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Bell, Search, Menu } from 'lucide-react';
import { useState } from 'react';

const PAGE_TITLES = {
  '/': 'Dashboard',
  '/home': 'Dashboard',
  '/library': 'Library',
  '/search': 'Library Search',
  '/upload': 'Upload Book',
  '/import': 'Import from Google Books',
  '/admin': 'Admin Panel',
};

export default function Topbar({ onToggleSidebar = null }) {
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');

  let title = PAGE_TITLES[location.pathname] || 'E-Library';
  if (location.pathname.startsWith('/book/')) title = 'Book Details';
  if (location.pathname.startsWith('/google-books/')) title = 'Google Books Preview';
  if (location.pathname.startsWith('/library/category/')) title = 'Category';

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button type="button" className="topbar-menu-btn" onClick={onToggleSidebar} aria-label="Open navigation menu">
          <Menu size={18} />
        </button>
        <h1 className="topbar-title">{title}</h1>
      </div>
      <div className="topbar-actions">
        <form className="topbar-search" onSubmit={handleSearch}>
          <Search size={16} className="topbar-search-icon" />
          <input
            type="text"
            placeholder="Search books..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </form>
        {user && (
          <>
            <button className="topbar-bell">
              <Bell size={18} />
            </button>
            <div className="topbar-user-avatar">
              {user.full_name?.[0]?.toUpperCase() || 'U'}
            </div>
          </>
        )}
      </div>
    </header>
  );
}
