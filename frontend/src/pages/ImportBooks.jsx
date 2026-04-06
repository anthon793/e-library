import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getArchiveCategories, triggerAutoImport, getAutoImportStatus, verifyImportedBooks, cleanupOfftopicBooks } from '../api/client';
import { Search, Globe, CheckCircle, BookOpen } from 'lucide-react';

export default function ImportBooks() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [categories, setCategories] = useState([]);
  const [categorySlug, setCategorySlug] = useState('');
  const [field, setField] = useState('subject');
  const [maxResultsPerSource, setMaxResultsPerSource] = useState(8);
  const [loading, setLoading] = useState(false);
  const [job, setJob] = useState(null);
  const [status, setStatus] = useState(null);
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [verifyResult, setVerifyResult] = useState(null);
  const [cleanupLoading, setCleanupLoading] = useState(false);

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

    const selectedCategory = categories.find((c) => c.slug === categorySlug);
    const confirmMessage = [
      'Start Google Books import?',
      `Query: ${query.trim()}`,
      `Field: ${field}`,
      `Category: ${selectedCategory?.name || categorySlug}`,
      `Max results: ${Number(maxResultsPerSource) || 8}`,
      'This will import Google Books only and add the books to the library with the selected category tag.',
    ].join('\n');

    if (!window.confirm(confirmMessage)) {
      return;
    }

    setLoading(true);
    setVerifyResult(null);
    try {
      const created = await triggerAutoImport(query, categorySlug, field, Number(maxResultsPerSource) || 8);
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

  const handleVerify = async () => {
    if (!categorySlug) {
      alert('Select a category first.');
      return;
    }

    setVerifyLoading(true);
    try {
      const result = await verifyImportedBooks(categorySlug, 25);
      setVerifyResult(result);
    } catch {
      alert('Failed to verify imported books.');
    } finally {
      setVerifyLoading(false);
    }
  };

  const handleCleanup = async () => {
    if (!categorySlug) {
      alert('Select a category first.');
      return;
    }

    if (!window.confirm('Remove off-topic Google books from this category?')) {
      return;
    }

    setCleanupLoading(true);
    try {
      const result = await cleanupOfftopicBooks(categorySlug);
      alert(`Cleanup complete. Removed ${result.removed || 0} off-topic books.`);
    } catch {
      alert('Failed to clean off-topic books.');
    } finally {
      setCleanupLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Google Books Auto Import</h1>
        <p className="page-subtitle">Fetch Google Books only, confirm the import, and store tagged books in the library</p>
      </div>

      <div className="form-group" style={{ maxWidth: 280, marginBottom: 16 }}>
        <label>Import into Category</label>
        <select value={categorySlug} onChange={(e) => setCategorySlug(e.target.value)} required>
          <option value="">Select category</option>
          {categories.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}
        </select>
      </div>

      <div className="form-group" style={{ maxWidth: 280, marginBottom: 16 }}>
        <label>Google Books Field</label>
        <select value={field} onChange={(e) => setField(e.target.value)} required>
          <option value="all">All</option>
          <option value="subject">Subject</option>
          <option value="title">Title</option>
          <option value="author">Author</option>
          <option value="isbn">ISBN</option>
        </select>
      </div>

      <div className="form-group" style={{ maxWidth: 280, marginBottom: 16 }}>
        <label>Max Results</label>
        <input type="number" min="1" max="30" value={maxResultsPerSource} onChange={(e) => setMaxResultsPerSource(e.target.value)} />
      </div>

      <form className="search-form" onSubmit={handleImport}>
        <div className="search-input-wrap">
          <Search size={18} className="search-input-icon" />
          <input type="text" placeholder="Search query (e.g. machine learning, cybersecurity)" value={query} onChange={(e) => setQuery(e.target.value)} autoFocus />
        </div>
        <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Importing...' : 'Start Google Import'}</button>
      </form>

      <div style={{ marginTop: 10 }}>
        <button type="button" className="btn btn-secondary btn-sm" onClick={handleCleanup} disabled={cleanupLoading}>
          {cleanupLoading ? 'Cleaning...' : 'Clean Off-Topic Books'}
        </button>
      </div>

      {status ? (
        <div className="card" style={{ padding: 16, marginTop: 16 }}>
          <h3 style={{ marginBottom: 8 }}>Import Job Status</h3>
          <p><strong>State:</strong> {status.status}</p>
          <p><strong>Checked Google Results:</strong> {status.checked_count || 0}</p>
          <p><strong>Imported Books:</strong> {status.imported_count || 0}</p>
          {(status.errors || []).length > 0 && (
            <p><strong>Errors:</strong> {(status.errors || []).slice(0, 3).join(' | ')}</p>
          )}
          {status.status === 'completed' && (
            <>
              <p className="imported-badge" style={{ marginTop: 8 }}><CheckCircle size={16} /> Completed</p>
              <button type="button" className="btn btn-secondary btn-sm" style={{ marginTop: 10 }} onClick={handleVerify} disabled={verifyLoading}>
                {verifyLoading ? 'Verifying...' : 'Verify Imported Books'}
              </button>
            </>
          )}

          {verifyResult && (
            <div style={{ marginTop: 12 }}>
              <h4 style={{ marginBottom: 8 }}>Verification Summary</h4>
              <p><strong>Total checked:</strong> {verifyResult.total_checked || 0}</p>
              <p><strong>Working:</strong> {verifyResult.working || 0}</p>
              <p><strong>Restricted:</strong> {verifyResult.restricted || 0}</p>
              <p><strong>Missing ID:</strong> {verifyResult.missing_identifier || 0}</p>
              <p><strong>Not Found:</strong> {verifyResult.not_found || 0}</p>
              <p><strong>Errors:</strong> {verifyResult.errors || 0}</p>
            </div>
          )}
        </div>
      ) : (
        <div className="empty-state">
          <Globe size={48} strokeWidth={1} />
          <h3>Start Google Books Import</h3>
          <p>Enter a query, choose a field and category, then confirm to import Google Books into the library.</p>
        </div>
      )}
    </div>
  );
}
