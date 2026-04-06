import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, BookOpen, ExternalLink, Eye, Info, BookMarked, Search as SearchIcon } from 'lucide-react';
import { getGoogleBook, getGoogleBookViewer } from '../api/client';
import GoogleBooksViewer from '../components/GoogleBooksViewer';

export default function GoogleBookDetail() {
  const { volumeId } = useParams();
  const [book, setBook] = useState(null);
  const [viewer, setViewer] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      setLoading(true);
      try {
        const details = await getGoogleBook(volumeId);
        if (cancelled) return;
        setBook(details);

        try {
          const viewerData = await getGoogleBookViewer(volumeId);
          if (!cancelled) {
            setViewer(viewerData);
          }
        } catch {
          if (!cancelled) {
            setViewer(null);
          }
        }
      } catch {
        if (!cancelled) {
          setBook(null);
          setViewer(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [volumeId]);

  if (loading) {
    return <div className="loading-center"><div className="spinner" /></div>;
  }

  if (!book) {
    return (
      <div className="empty-state">
        <BookOpen size={48} strokeWidth={1} />
        <h3>Google Books title not found</h3>
        <p><Link to="/search">Return to search</Link> and try another query.</p>
      </div>
    );
  }

  const googleIdentifier = viewer?.volumeId || book.volumeId || book.volume_id || '';
  const hasPreview = Boolean(googleIdentifier && (viewer?.pdf_viewable ?? viewer?.pdfViewable ?? book.pdf_viewable ?? viewer?.embeddable ?? book.embeddable ?? book.preview_available));
  const authors = Array.isArray(book.authors) && book.authors.length ? book.authors.join(', ') : book.author || 'Unknown Author';
  const categories = Array.isArray(book.categories) ? book.categories : [];

  return (
    <div className="google-book-detail-page">
      <Link to="/search" className="back-link"><ArrowLeft size={16} /> Back to Search</Link>

      <div className="detail-hero google-book-detail-hero">
        <div className="detail-hero-cover google-book-detail-cover">
          {book.cover_image ? (
            <img src={book.cover_image} alt={book.title} loading="eager" decoding="async" fetchPriority="high" onError={(e) => { e.currentTarget.style.display = 'none'; if (e.currentTarget.nextSibling) e.currentTarget.nextSibling.style.display = 'flex'; }} />
          ) : null}
          <div className="detail-hero-no-cover" style={book.cover_image ? { display: 'none' } : {}}>
            <BookMarked size={36} />
            <span style={{ fontWeight: 600, textAlign: 'center', fontSize: '0.9rem' }}>{book.title}</span>
          </div>
        </div>

        <div className="detail-hero-info">
          <div className="detail-hero-badges">
            {categories[0] && <span className="meta-pill pill-green"><Info size={12} /> {categories[0]}</span>}
            <span className="meta-pill pill-blue">Google Books</span>
            {hasPreview ? <span className="meta-pill pill-gray">PDF viewable</span> : <span className="meta-pill pill-gray">Preview blocked</span>}
          </div>

          <h1 className="detail-hero-title">{book.title}</h1>
          <p className="detail-hero-author">{authors}</p>

          <div className="detail-quick-stats">
            <div className="quick-stat"><Eye size={16} /><span><strong>{hasPreview ? 'Yes' : 'No'}</strong> PDF viewable</span></div>
            <div className="quick-stat"><SearchIcon size={16} /><span><strong>{book.page_count || '—'}</strong> Pages</span></div>
            <div className="quick-stat"><Info size={16} /><span><strong>{book.published_date || '—'}</strong> Published</span></div>
          </div>

          <div className="detail-hero-actions">
            {hasPreview && (
              <a className="btn btn-primary" href="#google-books-viewer">
                <Eye size={16} /> Read Preview
              </a>
            )}
            {book.info_link && (
              <a className="btn btn-secondary" href={book.info_link} target="_blank" rel="noreferrer noopener">
                <ExternalLink size={16} /> Google Books
              </a>
            )}
          </div>
        </div>
      </div>

      <div className="google-book-detail-grid">
        <div className="detail-about card">
          <div className="detail-description">
            <h3>Description</h3>
            <p>{book.description || 'No description is available for this title.'}</p>
          </div>

          <div className="detail-meta-grid">
            <div className="meta-item">
              <div className="meta-item-label">Title</div>
              <div className="meta-item-value">{book.title}</div>
            </div>
            <div className="meta-item">
              <div className="meta-item-label">Author</div>
              <div className="meta-item-value">{authors}</div>
            </div>
            <div className="meta-item">
              <div className="meta-item-label">Publisher</div>
              <div className="meta-item-value">{book.publisher || '—'}</div>
            </div>
            <div className="meta-item">
              <div className="meta-item-label">Published</div>
              <div className="meta-item-value">{book.published_date || '—'}</div>
            </div>
            <div className="meta-item">
              <div className="meta-item-label">ISBN-13</div>
              <div className="meta-item-value">{book.isbn_13 || '—'}</div>
            </div>
            <div className="meta-item">
              <div className="meta-item-label">Viewability</div>
              <div className="meta-item-value">{book.viewability || 'Unknown'}</div>
            </div>
          </div>
        </div>

        <div className="detail-preview card" id="google-books-viewer">
          {hasPreview ? (
            <div className="reader-embed reader-embed-surface google-book-viewer-shell">
              <GoogleBooksViewer identifier={googleIdentifier} />
              <div className="reader-footer">
                <p>Use the embedded Google Books viewer to flip pages, zoom, and search inside this PDF-viewable preview.</p>
              </div>
            </div>
          ) : (
            <div className="empty-state" style={{ padding: '44px 24px' }}>
              <BookOpen size={48} strokeWidth={1} />
              <h3>No PDF-viewable preview</h3>
              <p>This title exists in Google Books, but it is not available as an embeddable PDF-viewable preview.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}