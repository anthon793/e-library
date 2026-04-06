import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, BookOpen, ExternalLink, LoaderCircle, FileText, ShieldCheck, Clock3 } from 'lucide-react';
import { getBook, getBookStreamUrl } from '../api/client';
import GoogleBooksViewer from '../components/GoogleBooksViewer';
import { extractGoogleBooksVolumeId } from '../utils/googleBooks';

export default function ReadBook() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const initialBook = location.state?.book || null;
  const [book, setBook] = useState(null);
  const [loading, setLoading] = useState(!initialBook);
  const [isMobileView, setIsMobileView] = useState(() => window.innerWidth <= 768);

  useEffect(() => {
    const onResize = () => setIsMobileView(window.innerWidth <= 768);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    let cancelled = false;

    if (initialBook && String(initialBook.id) === String(id)) {
      setBook(initialBook);
      setLoading(false);
      return () => {
        cancelled = true;
      };
    }

    (async () => {
      setLoading(true);
      const data = await getBook(id).catch(() => null);
      if (cancelled) return;
      setBook(data);
      setLoading(false);
    })();

    return () => {
      cancelled = true;
    };
  }, [id, initialBook]);

  const readerUrl = getBookStreamUrl(id);
  const isGoogleBooks = String(book?.source || '').toLowerCase().includes('google books');
  const googleIdentifier = extractGoogleBooksVolumeId(book);

  if (loading) {
    return (
      <div className="loading-center">
        <LoaderCircle size={40} className="spinner" />
      </div>
    );
  }

  if (!book) {
    return (
      <div className="empty-state">
        <BookOpen size={48} strokeWidth={1} />
        <h3>Book not found</h3>
      </div>
    );
  }

  if (isMobileView) {
    return (
      <div className="mobile-reader-page">
        <div className="mobile-reader-topbar">
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => navigate('/library')}>
            <ArrowLeft size={14} /> Close
          </button>
          <span className="mobile-reader-title">{book.title}</span>
        </div>

        <div className="mobile-reader-canvas">
          {isGoogleBooks ? (
            <GoogleBooksViewer identifier={googleIdentifier} />
          ) : (
            <iframe
              src={readerUrl}
              title={`Read: ${book.title}`}
              width="100%"
              height="100%"
              frameBorder="0"
              allowFullScreen
            />
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="book-detail-page">
      <Link to={`/book/${book.id}`} className="back-link">
        <ArrowLeft size={16} /> Back to Details
      </Link>

      <div className="detail-hero reader-hero" style={{ marginBottom: 24 }}>
        <div className="detail-hero-cover">
          {book.cover_image ? (
            <img
              src={book.cover_image}
              alt={book.title}
              loading="eager"
              decoding="async"
              fetchPriority="high"
              onError={(e) => {
                e.currentTarget.style.display = 'none';
                if (e.currentTarget.nextSibling) e.currentTarget.nextSibling.style.display = 'flex';
              }}
            />
          ) : null}
          <div className="detail-hero-no-cover" style={book.cover_image ? { display: 'none' } : {}}>
            <span style={{ fontSize: '3.5rem' }}>📚</span>
            <span style={{ fontWeight: 600, textAlign: 'center', fontSize: '0.9rem' }}>{book.title}</span>
          </div>
        </div>

        <div className="detail-hero-info">
          <div className="detail-hero-badges">
            <span className="meta-pill pill-green">{book.category_name || 'Uncategorized'}</span>
            <span className="meta-pill pill-blue">{(book.book_type || 'hybrid').toUpperCase()}</span>
            {book.source && <span className="meta-pill pill-gray">{book.source}</span>}
          </div>
          <h1 className="detail-hero-title">{book.title}</h1>
          <p className="detail-hero-author">{book.author}</p>
          <div className="reader-status-row">
            <div className="reader-status-chip"><FileText size={14} /> Ready to read</div>
            <div className="reader-status-chip"><ShieldCheck size={14} /> Embedded preview</div>
            <div className="reader-status-chip"><Clock3 size={14} /> Fast loading</div>
          </div>
          <div className="detail-hero-actions">
            <a className="btn btn-secondary" href={readerUrl} target="_blank" rel="noreferrer noopener">
              <ExternalLink size={16} /> Open PDF in New Tab
            </a>
          </div>
        </div>
      </div>

      <div className="reader-shell card">
        <div className="reader-shell-header">
          <div>
            <h2>Read PDF</h2>
            <p>
              {isGoogleBooks
                ? 'Use the embedded Google Books viewer below to preview available pages.'
                : 'Use the embedded viewer below. Only direct PDF files are rendered in this reader.'}
            </p>
          </div>
          <div className="reader-shell-meta">
            <span>{book.source || 'Hybrid'}</span>
            <span>{book.category_name || 'Uncategorized'}</span>
          </div>
        </div>

        <div className="reader-embed reader-embed-surface">
          {isGoogleBooks ? (
            <>
              <GoogleBooksViewer identifier={googleIdentifier} />
              <div className="reader-footer">
                <p>If the viewer cannot open this title, Google Books may not allow embedded preview for this specific volume.</p>
              </div>
            </>
          ) : (
            <>
              <iframe
                src={readerUrl}
                title={`Read: ${book.title}`}
                width="100%"
                height="760"
                frameBorder="0"
                allowFullScreen
              />
              <div className="reader-footer">
                <p>If preview fails, this book currently has no direct PDF stream available.</p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
