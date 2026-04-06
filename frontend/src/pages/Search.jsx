import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { searchBooks } from '../api/client';
import BookCard from '../components/BookCard';
import { Search as SearchIcon, BookOpen, SlidersHorizontal } from 'lucide-react';

const SEARCH_FIELDS = [
  { value: 'cybersecurity', label: 'Cybersecurity' },
  { value: 'data-science', label: 'Data Science' },
  { value: 'artificial-intelligence', label: 'Artificial Intelligence' },
  { value: 'information-systems', label: 'Information Systems' },
  { value: 'computer-science', label: 'Computer Science' },
];

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [field, setField] = useState(searchParams.get('field') || 'cybersecurity');
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    const q = searchParams.get('q');
    const nextField = searchParams.get('field') || 'cybersecurity';
    setField(nextField);
    if (q) {
      setQuery(q);
      doSearch(q, nextField);
    }
  }, [searchParams]);

  const doSearch = async (q, nextField = field) => {
    if (!q.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const results = await searchBooks(q, nextField);
      setBooks(results);
    } catch {
      setBooks([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const params = new URLSearchParams();
    params.set('q', query);
    if (field && field !== 'all') {
      params.set('field', field);
    }
    setSearchParams(params);
    doSearch(query, field);
  };

  return (
    <div className="google-books-search-page">
      <div className="page-header">
        <h1>Library Search</h1>
        <p className="page-subtitle">Search books from your library and filter by Cybersecurity, Data Science, Artificial Intelligence, Information Systems, or Computer Science</p>
      </div>

      <form className="search-form" onSubmit={handleSubmit}>
        <div className="search-field-wrap">
          <SlidersHorizontal size={16} className="search-input-icon" />
          <select value={field} onChange={(e) => setField(e.target.value)} className="search-select">
            {SEARCH_FIELDS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>
        <div className="search-input-wrap">
          <SearchIcon size={18} className="search-input-icon" />
          <input
            type="text"
            placeholder="Search for books..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
        </div>
        <button type="submit" className="btn btn-primary">Search</button>
      </form>

      <p className="search-hint">
        Results come from your internal library database and are filtered by the selected field.
      </p>

      {loading ? (
        <div className="loading-center"><div className="spinner" /></div>
      ) : books.length > 0 ? (
        <>
          <p style={{ color: '#6B7280', marginBottom: 20, fontSize: '0.9rem' }}>
            Found <strong>{books.length}</strong> result(s) for "<strong>{searchParams.get('q')}</strong>" in <strong>{SEARCH_FIELDS.find((f) => f.value === field)?.label || field}</strong>
          </p>
          <div className="book-grid">
            {books.map((book) => <BookCard key={book.id} book={book} />)}
          </div>
        </>
      ) : searched ? (
        <div className="empty-state">
          <SearchIcon size={48} strokeWidth={1} />
          <h3>No results found</h3>
          <p>Try different keywords in the selected field.</p>
        </div>
      ) : (
        <div className="empty-state">
          <BookOpen size={48} strokeWidth={1} />
          <h3>Search Library Books</h3>
          <p>Enter a search term to find books from your library by the selected field.</p>
        </div>
      )}
    </div>
  );
}
