import { Link } from 'react-router-dom';
import { Download } from 'lucide-react';
import { useState } from 'react';

export default function BookCard({ book }) {
  const [imgLoaded, setImgLoaded] = useState(false);
  const [imgError, setImgError] = useState(false);
  const typeLabel = (book.book_type || 'hybrid').replace('-', ' ');

  return (
    <Link to={`/book/${book.id}/read`} state={{ book }} className="book-card">
      <div className="book-card-cover">
        {book.cover_image && !imgError ? (
          <>
            {!imgLoaded && <div className="book-card-skeleton" />}
            <img
              src={book.cover_image}
              alt={book.title}
              loading="lazy"
              decoding="async"
              fetchPriority="low"
              onLoad={() => setImgLoaded(true)}
              onError={() => setImgError(true)}
              style={{ opacity: imgLoaded ? 1 : 0 }}
            />
          </>
        ) : (
          <div className="book-card-no-cover">
            <span className="book-icon">📚</span>
            <span className="book-fallback-title">{book.title}</span>
          </div>
        )}
        <span className={`book-type-tag type-${book.book_type || 'hybrid'}`}>{typeLabel}</span>
      </div>
      <div className="book-card-body">
        <h3 className="book-card-title">{book.title}</h3>
        <p className="book-card-author">{book.author}</p>
        <div className="book-card-footer">
          <span className="book-card-category">{book.category_name || 'General'}</span>
          <span className="book-card-downloads">
            <Download size={12} /> {book.download_count || 0}
          </span>
        </div>
      </div>
    </Link>
  );
}
