import { Link } from 'react-router-dom';
import { Eye, ExternalLink, BookOpen } from 'lucide-react';

export default function GoogleBookCard({ book }) {
  const volumeId = book.volumeId || book.volume_id || '';
  const embeddable = Boolean(book.pdf_viewable ?? book.embeddable ?? book.preview_available);
  const authors = Array.isArray(book.authors) && book.authors.length
    ? book.authors.join(', ')
    : book.author || 'Unknown Author';

  return (
    <div className="book-card google-book-card">
      <Link to={`/google-books/${encodeURIComponent(volumeId)}`} className="google-book-cover-link">
        <div className="book-card-cover google-book-cover">
          {book.cover_image ? (
            <img src={book.cover_image} alt={book.title} loading="lazy" decoding="async" fetchPriority="low" />
          ) : (
            <div className="book-card-no-cover">
              <BookOpen size={28} />
              <span className="book-fallback-title">{book.title}</span>
            </div>
          )}
          <span className={`book-type-tag ${embeddable ? 'type-google-preview' : 'type-google-locked'}`}>
            {embeddable ? 'PDF Viewable' : 'Blocked'}
          </span>
        </div>
      </Link>

      <div className="book-card-body">
        <h3 className="book-card-title">{book.title}</h3>
        <p className="book-card-author">{authors}</p>
        <p className="google-book-snippet">{book.description || 'No description available.'}</p>
        <div className="book-card-footer">
          <span className="book-card-category">{book.category_name || 'Google Books'}</span>
          <span className="book-card-downloads">Google Books</span>
        </div>
        <div className="book-card-actions">
          <Link to={`/google-books/${encodeURIComponent(volumeId)}`} className="btn btn-primary btn-sm">
            <Eye size={14} /> Preview / Read
          </Link>
          {book.info_link && (
            <a href={book.info_link} target="_blank" rel="noreferrer noopener" className="btn btn-secondary btn-sm">
              <ExternalLink size={14} /> Source
            </a>
          )}
        </div>
      </div>
    </div>
  );
}