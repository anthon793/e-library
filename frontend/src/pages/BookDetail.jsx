import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getBook, getBookStreamUrl, getBookReadUrl, downloadBook } from '../api/client';
import { ArrowLeft, Download, BookOpen, Eye, Tag, Layers, User, Info } from 'lucide-react';
import GoogleBooksViewer from '../components/GoogleBooksViewer';
import { extractGoogleBooksVolumeId } from '../utils/googleBooks';

export default function BookDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [book, setBook] = useState(null);
  const [loadedBookId, setLoadedBookId] = useState(null);
  const [activeTab, setActiveTab] = useState('about');

  useEffect(() => {
    let cancelled = false;

    (async () => {
      const data = await getBook(id).catch(() => null);
      if (cancelled) return;
      setBook(data);
      setLoadedBookId(Number(id));
    })();

    return () => {
      cancelled = true;
    };
  }, [id]);

  const loading = loadedBookId !== Number(id);
  const bookViewUrl = getBookStreamUrl(id);
  const supportsInlineReader = !!book && (book.preview_link || book.book_type === 'upload' || book.book_type === 'archive' || book.book_type === 'hybrid');
  const isGoogleBooks = String(book?.source || '').toLowerCase().includes('google books');
  const googleIdentifier = extractGoogleBooksVolumeId(book);
  const canUseGoogleViewer = Boolean(isGoogleBooks && googleIdentifier);

  const handleDownload = async () => {
    try {
      await downloadBook(book.id);
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  const handleReadNow = () => {
    navigate(getBookReadUrl(book.id), { state: { book } });
  };

  if (loading) return <div className="loading-center"><div className="spinner" /></div>;
  if (!book) return <div className="empty-state"><h3>Book not found</h3></div>;

  return (
    <div className="book-detail-page">
      <Link to="/library" className="back-link"><ArrowLeft size={16} /> Back to Library</Link>

      {/* Hero Section */}
      <div className="detail-hero">
        <div className="detail-hero-cover">
          {book.cover_image ? (
            <img src={book.cover_image} alt={book.title} loading="eager" decoding="async" fetchPriority="high" onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }} />
          ) : null}
          <div className="detail-hero-no-cover" style={book.cover_image ? { display: 'none' } : {}}>
            <span style={{ fontSize: '3.5rem' }}>📚</span>
            <span style={{ fontWeight: 600, textAlign: 'center', fontSize: '0.9rem' }}>{book.title}</span>
          </div>
        </div>

        <div className="detail-hero-info">
          <div className="detail-hero-badges">
            {book.category_name && <span className="meta-pill pill-green"><Tag size={12} /> {book.category_name}</span>}
            <span className="meta-pill pill-blue">{book.book_type?.toUpperCase()}</span>
            {book.source && <span className="meta-pill pill-gray">{book.source}</span>}
          </div>

          <h1 className="detail-hero-title">{book.title}</h1>
          <p className="detail-hero-author"><User size={14} /> {book.author}</p>

          {/* Quick Stats */}
          <div className="detail-quick-stats">
            <div className="quick-stat">
              <Download size={16} />
              <span><strong>{book.download_count || 0}</strong> Downloads</span>
            </div>
            <div className="quick-stat">
              <Layers size={16} />
              <span><strong>{book.book_type}</strong> Type</span>
            </div>
            {book.source && (
              <div className="quick-stat">
                <Info size={16} />
                <span><strong>{book.source}</strong> Source</span>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="detail-hero-actions">
            {(supportsInlineReader || book.preview_link || book.download_link) && (
              <button className="btn btn-primary" onClick={handleReadNow}>
                <Eye size={16} /> Read PDF
              </button>
            )}
            {(book.book_type === 'upload' || book.book_type === 'archive' || book.book_type === 'hybrid') && (
              <button className="btn btn-primary" onClick={handleDownload}>
                <Download size={16} /> Download PDF
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="detail-tabs">
        <button type="button" className={`detail-tab ${activeTab === 'about' ? 'active' : ''}`} onClick={() => setActiveTab('about')}>
          <Info size={15} /> About This Book
        </button>
        {supportsInlineReader && (
          <button type="button" className={`detail-tab ${activeTab === 'preview' ? 'active' : ''}`} onClick={() => setActiveTab('preview')}>
            <Eye size={15} /> Read PDF
          </button>
        )}
      </div>

      {/* Tab Content */}
      {activeTab === 'about' && (
        <div className="detail-about card">
          {book.description ? (
            <div className="detail-description">
              <h3>Description</h3>
              <p>{book.description}</p>
            </div>
          ) : (
            <div className="detail-description">
              <h3>Description</h3>
              <p className="no-desc-text">
                No description available for this book. 
                {book.view_link && (
                  <> Visit <a href={book.view_link} target="_blank" rel="noopener noreferrer">the source page</a> for more information.</>
                )}
              </p>
            </div>
          )}

          {/* Book Metadata Grid */}
          <div className="detail-meta-grid">
            <div className="meta-item">
              <div className="meta-item-label">Category</div>
              <div className="meta-item-value">{book.category_name || 'Uncategorized'}</div>
            </div>
            <div className="meta-item">
              <div className="meta-item-label">Author</div>
              <div className="meta-item-value">{book.author}</div>
            </div>
            <div className="meta-item">
              <div className="meta-item-label">Source</div>
              <div className="meta-item-value">{book.source || 'Local'}</div>
            </div>
            <div className="meta-item">
              <div className="meta-item-label">Type</div>
              <div className="meta-item-value">{book.book_type}</div>
            </div>
            <div className="meta-item">
              <div className="meta-item-label">Downloads</div>
              <div className="meta-item-value">{book.download_count || 0}</div>
            </div>
            <div className="meta-item">
              <div className="meta-item-label">Added</div>
              <div className="meta-item-value">{book.created_at?.split('T')[0] || '—'}</div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'preview' && (
        <div className="detail-preview card">
          {supportsInlineReader ? (
            <div className="reader-embed">
              {canUseGoogleViewer ? (
                <>
                  <GoogleBooksViewer identifier={googleIdentifier} />
                  <div className="reader-footer">
                    <p>This preview is rendered by Google Embedded Viewer using volume ID.</p>
                  </div>
                </>
              ) : (
                <>
                  <iframe
                    src={bookViewUrl}
                    title={`Read: ${book.title}`}
                    width="100%"
                    height="700"
                    frameBorder="0"
                    allowFullScreen
                  />
                  <div className="reader-footer">
                    <p>
                      {isGoogleBooks
                        ? 'Opening preview through the stream endpoint because a direct Google volume ID was not found for this record.'
                        : 'If preview fails, this book currently has no direct PDF stream available.'}
                    </p>
                  </div>
                </>
              )}
            </div>
          ) : (
            <div className="empty-state" style={{ padding: '40px' }}>
              <BookOpen size={48} strokeWidth={1} />
              <h3>No inline PDF reader</h3>
              <p>This source does not support inline PDF reading in this page.</p>
            </div>
          )}
        </div>
      )}

    </div>
  );
}
