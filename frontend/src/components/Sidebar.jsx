import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Home,
  BookOpen,
  Upload,
  Globe,
  LayoutDashboard,
  Search,
  LogIn,
  LogOut,
  ChevronDown,
  Shield,
  BarChart3,
  Brain,
  Network,
  Code,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { getArchiveCategories } from '../api/client';

const CATEGORY_ICONS = {
  'cybersecurity': Shield,
  'data-science': BarChart3,
  'artificial-intelligence': Brain,
  'information-systems': Network,
  'computer-science': Code,
};

function canonicalCategorySlug(cat) {
  const rawSlug = String(cat?.slug || '').trim().toLowerCase();
  const rawName = String(cat?.name || '').trim().toLowerCase();
  const token = rawSlug || rawName;

  if (token.includes('cyber')) return 'cybersecurity';
  if (token.includes('data')) return 'data-science';
  if (token.includes('artificial') || token === 'ai') return 'artificial-intelligence';
  if (token.includes('information') || token.includes('system')) return 'information-systems';
  if (token.includes('computer') || token === 'cs') return 'computer-science';

  return rawSlug;
}

function mergeSidebarCategories(items) {
  const merged = new Map();

  for (const cat of items || []) {
    const slug = canonicalCategorySlug(cat);
    if (!slug) continue;

    const current = merged.get(slug);
    if (!current) {
      merged.set(slug, {
        ...cat,
        id: slug,
        slug,
        book_count: Number(cat.book_count || 0),
      });
      continue;
    }

    current.book_count += Number(cat.book_count || 0);
  }

  return Array.from(merged.values());
}

export default function Sidebar({ onNavigate = null }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [catOpen, setCatOpen] = useState(false);

  useEffect(() => {
    getArchiveCategories().then((cats) => setCategories(mergeSidebarCategories(cats))).catch(() => {});
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/library');
    onNavigate?.();
  };

  const isLecturerOrAdmin = user && (user.role === 'lecturer' || user.role === 'admin');

  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="sidebar-logo">
          <img src="/vuna.png" alt="Logo" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        </div>
        <div>
          <div className="sidebar-brand-name">E-Library</div>
          <div className="sidebar-brand-sub">Academic Library</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <NavLink to="/" end onClick={() => onNavigate?.()} className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <Home size={18} /> <span>Home</span>
        </NavLink>

        <NavLink to="/home" end onClick={() => onNavigate?.()} className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <LayoutDashboard size={18} /> <span>Dashboard</span>
        </NavLink>

        <NavLink to="/library" end onClick={() => onNavigate?.()} className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <BookOpen size={18} /> <span>Library</span>
        </NavLink>

        <NavLink to="/search" onClick={() => onNavigate?.()} className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <Search size={18} /> <span>Search Books</span>
        </NavLink>

        {/* Categories Dropdown */}
        <button className="sidebar-link sidebar-dropdown-btn" onClick={() => setCatOpen(!catOpen)}>
          <LayoutDashboard size={18} /> <span>Categories</span>
          <ChevronDown size={16} className={`dropdown-arrow ${catOpen ? 'open' : ''}`} />
        </button>

        {catOpen && (
          <div className="sidebar-submenu">
            {categories.map((cat) => {
              const Icon = CATEGORY_ICONS[cat.slug] || BookOpen;
              return (
                <NavLink
                  key={cat.id}
                  to={`/library/category/${cat.slug}`}
                  onClick={() => onNavigate?.()}
                  className={({ isActive }) => `sidebar-sublink ${isActive ? 'active' : ''}`}
                >
                  <Icon size={15} />
                  <span>{cat.name}</span>
                  <span className="sidebar-badge">{cat.book_count}</span>
                </NavLink>
              );
            })}
          </div>
        )}

        {/* Divider */}
        <div className="sidebar-divider" />

        {/* Lecturer / Admin links */}
        {isLecturerOrAdmin && (
          <>
            <NavLink to="/upload" onClick={() => onNavigate?.()} className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
              <Upload size={18} /> <span>Upload Book</span>
            </NavLink>
            <NavLink to="/import" onClick={() => onNavigate?.()} className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
              <Globe size={18} /> <span>Import Books</span>
            </NavLink>
          </>
        )}

        {user?.role === 'admin' && (
          <NavLink to="/admin" onClick={() => onNavigate?.()} className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <LayoutDashboard size={18} /> <span>Admin Panel</span>
          </NavLink>
        )}
      </nav>

      {/* User Info at Bottom */}
      <div className="sidebar-footer">
        {user ? (
          <div className="sidebar-user">
            <div className="sidebar-user-avatar">{user.full_name?.[0]?.toUpperCase() || 'U'}</div>
            <div className="sidebar-user-info">
              <div className="sidebar-user-name">{user.full_name}</div>
              <div className="sidebar-user-role">{user.email}</div>
            </div>
            <span className={`role-badge role-${user.role}`}>{user.role}</span>
            <button className="sidebar-logout" onClick={handleLogout} title="Logout">
              <LogOut size={16} />
            </button>
          </div>
        ) : (
          <NavLink to="/login" onClick={() => onNavigate?.()} className="sidebar-login-btn">
            <LogIn size={18} /> <span>Login</span>
          </NavLink>
        )}
      </div>
    </aside>
  );
}
