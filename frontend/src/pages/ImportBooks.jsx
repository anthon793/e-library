import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getArchiveCategories, triggerAutoImport, getAutoImportStatus } from '../api/client';
import { Search, Globe, CheckCircle, BookOpen } from 'lucide-react';

export default function ImportBooks() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [categories, setCategories] = useState([]);
  const [categorySlug, setCategorySlug] = useState('');
  const [maxResultsPerSource, setMaxResultsPerSource] = useState(8);
  const [loading, setLoading] = useState(false);
  const [job, setJob] = useState(null);
  const [status, setStatus] = useState(null);

  useEffect(() => {
    if (!user || (user.role !== 'lecturer' && user.role !== 'admin')) {
      navigate('/login');
      return;
    }
    getArchiveCategories().then(setCategories).catch(() => {});
  }, [user]);

  useEffect(() => {
    if (!job?.job_id) return;
    let alive = true;
    const poll = async () => {
      try {
        const next = await getAutoImportStatus(job.job_id);
        if (!alive) return;
        setStatus(next);
        if (next.status === 'running' || next.status === 'queued') {
          setTimeout(poll, 1200);
        } else {
          setLoading(false);
        }
      } catch {
        if (!alive) return;
        setLoading(false);
      }
    };
    poll();
    return () => { alive = false; };
  }, [job]);

  const handleImport = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    if (!categorySlug) {
      alert('Select a category before starting auto-import.');
      return;
    }

    setLoading(true);
    try {
      const created = await triggerAutoImport(query, categorySlug, Number(maxResultsPerSource) || 8);
      setJob(created);
      setStatus({ status: created.status, imported_count: 0, checked_count: 0, errors: [] });
    } catch {
      setStatus(null);
      setJob(null);
      setLoading(false);
      alert('Failed to start auto-import.');
    } finally {
      if (!job) {
        // keep loading true while background status polls
      }
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Hybrid Auto Import</h1>
        <p className="page-subtitle">Fetch metadata from multiple sources, validate PDF links, and store verified books</p>
      </div>

      <div className="form-group" style={{ maxWidth: 280, marginBottom: 16 }}>
        <label>Import into Category</label>
        <select value={categorySlug} onChange={(e) => setCategorySlug(e.target.value)} required>
          <option value="">Select category</option>
          {categories.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}
        </select>
      </div>

      <div className="form-group" style={{ maxWidth: 280, marginBottom: 16 }}>
        <label>Max Results Per Source</label>
        <input type="number" min="1" max="30" value={maxResultsPerSource} onChange={(e) => setMaxResultsPerSource(e.target.value)} />
      </div>

      <form className="search-form" onSubmit={handleImport}>
        <div className="search-input-wrap">
          <Search size={18} className="search-input-icon" />
          <input type="text" placeholder="Search query (e.g. machine learning, cybersecurity)" value={query} onChange={(e) => setQuery(e.target.value)} autoFocus />
        </div>
        <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Importing...' : 'Start Auto Import'}</button>
      </form>

      {status ? (
        <div className="card" style={{ padding: 16, marginTop: 16 }}>
          <h3 style={{ marginBottom: 8 }}>Import Job Status</h3>
          <p><strong>State:</strong> {status.status}</p>
          <p><strong>Checked PDF Links:</strong> {status.checked_count || 0}</p>
          <p><strong>Imported Verified Books:</strong> {status.imported_count || 0}</p>
          {(status.errors || []).length > 0 && (
            <p><strong>Errors:</strong> {(status.errors || []).slice(0, 3).join(' | ')}</p>
          )}
          {status.status === 'completed' && (
            <p className="imported-badge" style={{ marginTop: 8 }}><CheckCircle size={16} /> Completed</p>
          )}
        </div>
      ) : (
        <div className="empty-state">
          <Globe size={48} strokeWidth={1} />
          <h3>Start Hybrid Import</h3>
          <p>Enter a query to fetch books from multiple sources and store only verified PDFs.</p>
        </div>
      )}
    </div>
  );
}
