import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getBooks, searchBooks } from '../api/client';
import BookCard from '../components/BookCard';
import { Search as SearchIcon, BookOpen, SlidersHorizontal } from 'lucide-react';

const SEARCH_FIELDS = [
  { value: 'all', label: 'ALL' },
  { value: 'cybersecurity', label: 'Cybersecurity' },
  { value: 'data-science', label: 'Data Science' },
  { value: 'artificial-intelligence', label: 'Artificial Intelligence' },
  { value: 'information-systems', label: 'Information Systems' },
  { value: 'computer-science', label: 'Computer Science' },
];

export default function Search() {
  const PAGE_SIZE = 100;
  const MAX_PAGES = 30;

  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [field, setField] = useState(searchParams.get('field') || 'all');
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(Boolean(searchParams.get('q')));

  useEffect(() => {
    const q = searchParams.get('q');
    const nextField = searchParams.get('field') || 'all';
    setField(nextField);
    setSearched(Boolean(q));

    if (q) {
      setQuery(q);
      doSearch(q, nextField);
      return;
    }

    setQuery('');
    loadBooksByField(nextField);
  }, [searchParams]);

  const getAllBooksForCategory = async (category = null) => {
    const allItems = [];
    let page = 0;

    while (page < MAX_PAGES) {
      const skip = page * PAGE_SIZE;
      const chunk = await getBooks(skip, PAGE_SIZE, category);
      if (!Array.isArray(chunk) || chunk.length === 0) break;

      allItems.push(...chunk);
      if (chunk.length < PAGE_SIZE) break;
      page += 1;
    }

    return allItems;
  };

  const loadBooksByField = async (nextField = field) => {
    setLoading(true);
    try {
      const category = nextField === 'all' ? null : nextField;
      const results = await getAllBooksForCategory(category);
      setBooks(results);
    } catch {
      setBooks([]);
    } finally {
      setLoading(false);
    }
  };

  const doSearch = async (q, nextField = field) => {
    if (!q.trim()) {
      await loadBooksByField(nextField);
      return;
    }

    setLoading(true);
    setSearched(true);
    try {
      const category = nextField === 'all' ? null : nextField;
      const results = await searchBooks(q, category);
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
    if (query.trim()) {
      params.set('q', query.trim());
    }
    if (field && field !== 'all') {
      params.set('field', field);
    }
    setSearchParams(params);
    doSearch(query, field);
  };

  const handleFieldChange = (nextField) => {
    setField(nextField);

    const params = new URLSearchParams();
    if (query.trim()) {
      params.set('q', query.trim());
    }
    if (nextField !== 'all') {
      params.set('field', nextField);
    }
    setSearchParams(params);

    if (query.trim()) {
      doSearch(query, nextField);
      return;
    }

    setSearched(false);
    loadBooksByField(nextField);
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
          <select value={field} onChange={(e) => handleFieldChange(e.target.value)} className="search-select">
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
        ALL shows all books by default. Selecting a field shows only books for that field before you type.
      </p>

      {loading ? (
        <div className="loading-center"><div className="spinner" /></div>
      ) : books.length > 0 ? (
        <>
          <p style={{ color: '#6B7280', marginBottom: 20, fontSize: '0.9rem' }}>
            {searched
              ? <>Found <strong>{books.length}</strong> result(s) for "<strong>{query}</strong>" in <strong>{SEARCH_FIELDS.find((f) => f.value === field)?.label || field}</strong></>
              : <>Showing <strong>{books.length}</strong> book(s) in <strong>{SEARCH_FIELDS.find((f) => f.value === field)?.label || field}</strong></>}
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
          <h3>No books in this filter</h3>
          <p>Try switching to ALL or another field.</p>
        </div>
      )}
    </div>
  );
}
