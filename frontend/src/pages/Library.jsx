import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getBooks, getArchiveCategories } from '../api/client';
import BookCard from '../components/BookCard';
import { BookOpen, ChevronLeft, ChevronRight } from 'lucide-react';

export default function Library() {
  const { slug } = useParams();
  const [books, setBooks] = useState([]);
  const [categories, setCategories] = useState([]);
  const [categoriesLoaded, setCategoriesLoaded] = useState(false);
  const [activeCat, setActiveCat] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const LIMIT = 20;

  useEffect(() => {
    getArchiveCategories()
      .then(setCategories)
      .catch(() => {})
      .finally(() => setCategoriesLoaded(true));
  }, []);

  useEffect(() => {
    if (!categoriesLoaded) return;

    setLoading(true);
    setPage(1);
    const cat = slug ? categories.find((c) => c.slug === slug) : null;
    setActiveCat(cat || null);

    getBooks(0, LIMIT, cat?.slug || null)
      .then(setBooks)
      .catch((err) => {
        console.error('Failed to load books:', err);
        setBooks([]);
      })
      .finally(() => setLoading(false));
  }, [slug, categories, categoriesLoaded]);

  const loadPage = (p) => {
    setLoading(true);
    getBooks((p - 1) * LIMIT, LIMIT, activeCat?.slug || null)
      .then(setBooks)
      .catch((err) => {
        console.error('Failed to load paged books:', err);
        setBooks([]);
      })
      .finally(() => setLoading(false));
    setPage(p);
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>{activeCat ? activeCat.name : 'All Books'}</h1>
          <p className="page-subtitle">{activeCat ? activeCat.description : 'Browse our complete collection of academic books'}</p>
        </div>
      </div>

      {loading ? (
        <div className="loading-center"><div className="spinner" /></div>
      ) : books.length > 0 ? (
        <>
          <div className="book-grid">
            {books.map((book) => <BookCard key={book.id} book={book} />)}
          </div>
          <div className="pagination">
            {page > 1 && (
              <button className="btn btn-secondary btn-sm" onClick={() => loadPage(page - 1)}>
                <ChevronLeft size={16} /> Previous
              </button>
            )}
            <span className="page-num">Page {page}</span>
            {books.length === LIMIT && (
              <button className="btn btn-secondary btn-sm" onClick={() => loadPage(page + 1)}>
                Next <ChevronRight size={16} />
              </button>
            )}
          </div>
        </>
      ) : (
        <div className="empty-state">
          <BookOpen size={48} strokeWidth={1} />
          <h3>No books found</h3>
          <p>{activeCat ? 'No books in this category yet.' : 'The library is empty.'}</p>
        </div>
      )}
    </div>
  );
}
