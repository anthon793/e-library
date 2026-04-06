import { useEffect, useRef, useState } from 'react';
import { LoaderCircle } from 'lucide-react';

const SCRIPT_ID = 'google-books-embedded-viewer-api';
const LOAD_TIMEOUT_MS = 20000;
const VIEWER_LOAD_TIMEOUT_MS = 26000;
const SPINNER_VISIBLE_MS = 4500;

let scriptLoadPromise = null;

function waitForDefaultViewer(timeoutMs = LOAD_TIMEOUT_MS) {
  return new Promise((resolve, reject) => {
    if (window.google?.books?.DefaultViewer) {
      resolve();
      return;
    }

    const started = Date.now();
    const poll = window.setInterval(() => {
      if (window.google?.books?.DefaultViewer) {
        window.clearInterval(poll);
        resolve();
        return;
      }
      if (Date.now() - started >= timeoutMs) {
        window.clearInterval(poll);
        reject(new Error('Timed out while loading Google Books viewer API'));
      }
    }, 50);
  });
}

function ensureGoogleBooksScript() {
  if (window.google?.books) {
    return Promise.resolve();
  }

  if (scriptLoadPromise) {
    return scriptLoadPromise;
  }

  scriptLoadPromise = new Promise((resolve, reject) => {
    const existingScript = document.getElementById(SCRIPT_ID);
    if (existingScript) {
      const started = Date.now();
      const poll = window.setInterval(() => {
        if (window.google?.books) {
          window.clearInterval(poll);
          resolve();
          return;
        }
        if (Date.now() - started >= LOAD_TIMEOUT_MS) {
          window.clearInterval(poll);
          reject(new Error('Timed out while loading Google Books script'));
        }
      }, 50);

      existingScript.addEventListener('error', () => {
        window.clearInterval(poll);
        reject(new Error('Failed to load Google Books Embedded Viewer API'));
      }, { once: true });
      return;
    }

    const script = document.createElement('script');
    script.id = SCRIPT_ID;
    script.src = 'https://www.google.com/books/jsapi.js';
    script.async = true;
    script.onload = () => {
      if (window.google?.books) {
        resolve();
      } else {
        reject(new Error('Google Books script loaded but API namespace is unavailable'));
      }
    };
    script.onerror = () => {
      reject(new Error('Failed to load Google Books Embedded Viewer API'));
    };
    document.head.appendChild(script);
  }).catch((err) => {
    // Allow retries after transient network/script failures.
    scriptLoadPromise = null;
    throw err;
  });

  return scriptLoadPromise;
}

function loadGoogleBooksApi() {
  return new Promise((resolve, reject) => {
    const api = window.google?.books;
    if (!api) {
      reject(new Error('Google Books API is not available.'));
      return;
    }

    if (window.google?.books?.DefaultViewer) {
      resolve();
      return;
    }

    if (typeof api.setOnLoadCallback !== 'function' || typeof api.load !== 'function') {
      resolve();
      return;
    }

    let settled = false;
    const finishResolve = () => {
      if (settled) return;
      settled = true;
      window.clearTimeout(deadline);
      window.clearInterval(poll);
      resolve();
    };

    const finishReject = (message) => {
      if (settled) return;
      settled = true;
      window.clearTimeout(deadline);
      window.clearInterval(poll);
      reject(new Error(message));
    };

    const poll = window.setInterval(() => {
      if (window.google?.books?.DefaultViewer) {
        finishResolve();
      }
    }, 100);

    const deadline = window.setTimeout(() => {
      finishReject('Timed out while loading Google Books API.');
    }, LOAD_TIMEOUT_MS);

    try {
      api.setOnLoadCallback(() => {
        if (window.google?.books?.DefaultViewer) {
          finishResolve();
        }
      });
      api.load();
    } catch {
      finishReject('Failed to initialize Google Books API.');
    }
  });
}

export default function GoogleBooksViewer({ identifier = '' }) {
  const containerRef = useRef(null);
  const initializedRef = useRef(false);
  const viewerRef = useRef(null);
  const settledRef = useRef(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showSpinner, setShowSpinner] = useState(true);
  const normalizedIdentifier = String(identifier || '').trim();
  const hasIdentifier = Boolean(normalizedIdentifier);

  useEffect(() => {
    if (!hasIdentifier) {
      setLoading(false);
      setError('');
      return undefined;
    }

    let cancelled = false;
    const watchdog = window.setTimeout(() => {
      if (!cancelled && !settledRef.current) {
        settledRef.current = true;
        setError('Google Books preview timed out while loading.');
        setLoading(false);
      }
    }, VIEWER_LOAD_TIMEOUT_MS);
    const spinnerTimer = window.setTimeout(() => {
      if (!cancelled && !settledRef.current) {
        setShowSpinner(false);
      }
    }, SPINNER_VISIBLE_MS);

    initializedRef.current = false;
    viewerRef.current = null;
    settledRef.current = false;

    async function initViewer() {
      try {
        setLoading(true);
        setError('');
        setShowSpinner(true);
        await ensureGoogleBooksScript();
        await loadGoogleBooksApi();
      await waitForDefaultViewer();

        if (cancelled || !containerRef.current || !window.google?.books?.DefaultViewer || initializedRef.current) return;

        initializedRef.current = true;

        containerRef.current.innerHTML = '';

        const viewer = new window.google.books.DefaultViewer(containerRef.current);
        viewerRef.current = viewer;
        viewer.load(
          normalizedIdentifier,
          () => {
            if (!cancelled) {
              settledRef.current = true;
              window.clearTimeout(spinnerTimer);
              setError('Google Books preview could not be embedded for this title.');
              setLoading(false);
            }
          },
          () => {
            if (!cancelled) {
              settledRef.current = true;
              window.clearTimeout(spinnerTimer);
              setError('');
              setLoading(false);
            }
          },
        );
      } catch (err) {
        if (!cancelled) {
          settledRef.current = true;
          window.clearTimeout(spinnerTimer);
          setError(err.message || 'Failed to load the embedded viewer.');
          setLoading(false);
        }
      }
    }

    initViewer();

    return () => {
      cancelled = true;
      window.clearTimeout(watchdog);
      window.clearTimeout(spinnerTimer);
    };
  }, [normalizedIdentifier, hasIdentifier]);

  if (!hasIdentifier) {
    return (
      <div className="empty-state" style={{ padding: 32 }}>
        <h3>No preview available</h3>
        <p>This title does not expose an embeddable Google Books preview.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state" style={{ padding: 32 }}>
        <h3>Preview unavailable</h3>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div style={{ position: 'relative', minHeight: 720 }}>
      {loading && (
        <div className="reader-loading-overlay">
          <div className="reader-loading-card">
            {showSpinner ? <LoaderCircle size={36} className="spinner" /> : <LoaderCircle size={36} />}
            <strong>Loading preview</strong>
            <span>{showSpinner ? 'Preparing the embedded Google Books viewer.' : 'Still loading. Finalizing viewer response.'}</span>
          </div>
        </div>
      )}
      <div className="google-books-canvas" ref={containerRef} />
    </div>
  );
}