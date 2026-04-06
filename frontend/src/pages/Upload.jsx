import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getArchiveCategories, uploadBook } from '../api/client';
import { Upload as UploadIcon, CheckCircle } from 'lucide-react';

export default function Upload() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState('');
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (authLoading) {
      return;
    }
    if (!user || (user.role !== 'lecturer' && user.role !== 'admin')) {
      navigate('/login');
      return;
    }
    getArchiveCategories().then(setCategories).catch(() => {});
  }, [user, authLoading, navigate]);

  if (authLoading) {
    return <div className="page-header"><h1>Loading...</h1></div>;
  }

  const handlePdfUpload = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    const formData = new FormData(e.target);
    try {
      await uploadBook(formData);
      setSuccess('Book uploaded successfully!');
      e.target.reset();
      setFileName('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-page">
      <div className="page-header">
        <h1>Upload Book</h1>
        <p className="page-subtitle">Upload a verified PDF into the hybrid library</p>
      </div>

      {success && <div className="alert alert-success"><CheckCircle size={16} /> {success}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <form className="upload-form card" onSubmit={handlePdfUpload}>
        <label className="file-drop-zone" htmlFor="pdf-file">
          <UploadIcon size={32} strokeWidth={1.5} />
          <p>{fileName || 'Drag & drop PDF here or click to browse'}</p>
          <span className="file-hint">Maximum file size: 50MB</span>
          <input type="file" id="pdf-file" name="file" accept=".pdf" required hidden onChange={(e) => setFileName(e.target.files[0]?.name || '')} />
        </label>
        <div className="form-group"><label>Title</label><input name="title" placeholder="Book title" required /></div>
        <div className="form-group"><label>Author</label><input name="author" placeholder="Author name" required /></div>
        <div className="form-group">
          <label>Category</label>
          <select name="category" required><option value="">Select category</option>{categories.map((c) => <option key={c.slug} value={c.name}>{c.name}</option>)}</select>
        </div>
        <div className="form-group"><label>Publisher (optional)</label><input name="publisher" placeholder="Publisher" /></div>
        <div className="form-group"><label>Published Year (optional)</label><input name="published_year" placeholder="2024" /></div>
        <div className="form-group"><label>Cover Image URL (optional)</label><input name="cover_image" type="url" placeholder="https://..." /></div>
        <div className="form-group"><label>Description</label><textarea name="description" placeholder="Brief description..." rows={3} /></div>
        <button type="submit" className="btn btn-primary btn-full" disabled={loading}>{loading ? 'Uploading...' : 'Upload Book'}</button>
      </form>
    </div>
  );
}
