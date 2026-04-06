import { Link } from 'react-router-dom';
import { useRef, useState } from 'react';
import { ChevronRight, ChevronDown, Shield, Brain, BarChart3, Network, Code2, BookOpen } from 'lucide-react';

const PROGRAMS = [
  {
    name: 'Computer Science',
    slug: 'computer-science',
    icon: Code2,
    blurb: 'Algorithms, software engineering, and computing fundamentals.',
  },
  {
    name: 'Information Systems',
    slug: 'information-systems',
    icon: Network,
    blurb: 'Enterprise systems, MIS, databases, and business technology.',
  },
  {
    name: 'Data Science',
    slug: 'data-science',
    icon: BarChart3,
    blurb: 'Data analysis, machine learning, and real-world insights.',
  },
  {
    name: 'Artificial Intelligence',
    slug: 'artificial-intelligence',
    icon: Brain,
    blurb: 'Deep learning, intelligent systems, and AI applications.',
  },
  {
    name: 'Cybersecurity',
    slug: 'cybersecurity',
    icon: Shield,
    blurb: 'Digital defense, ethical hacking, and secure infrastructures.',
  },
];

const PROGRAM_LINKS = PROGRAMS.map((program) => ({
  label: program.name,
  to: `/library/category/${program.slug}`,
}));

export default function Landing() {
  const [programsOpen, setProgramsOpen] = useState(false);
  const programsMenuRef = useRef(null);

  const closeProgramsIfOutside = (event) => {
    const nextTarget = event.relatedTarget;
    if (!programsMenuRef.current || !nextTarget) {
      setProgramsOpen(false);
      return;
    }
    if (!programsMenuRef.current.contains(nextTarget)) {
      setProgramsOpen(false);
    }
  };

  return (
    <div className="landing-page">
      <header className="landing-navbar">
        <div className="landing-nav-inner">
          <div className="landing-brand">
            <img className="landing-brand-logo" src="/vuna.png" alt="Veritas University logo" />
            <div>
              <p className="landing-brand-title">Veritas University</p>
              <p className="landing-brand-sub">Faculty of Natural and Applied Sciences</p>
            </div>
          </div>

          <nav className="landing-menu" aria-label="Primary">
            <Link to="/">Home</Link>
            <div
              className={`landing-menu-item ${programsOpen ? 'open' : ''}`}
              ref={programsMenuRef}
              onMouseEnter={() => setProgramsOpen(true)}
              onMouseLeave={() => setProgramsOpen(false)}
              onFocusCapture={() => setProgramsOpen(true)}
              onBlurCapture={closeProgramsIfOutside}
            >
              <button
                type="button"
                className="landing-menu-trigger"
                aria-haspopup="true"
                aria-expanded={programsOpen}
                onClick={() => setProgramsOpen((v) => !v)}
                onKeyDown={(event) => {
                  if (event.key === 'Escape') {
                    setProgramsOpen(false);
                  }
                }}
              >
                <span>Programs</span>
                <ChevronDown size={14} />
              </button>
              <div className="landing-menu-dropdown" role="menu" aria-label="Programs">
                {PROGRAM_LINKS.map((entry) => (
                  <Link key={entry.label} to={entry.to} onClick={() => setProgramsOpen(false)}>{entry.label}</Link>
                ))}
              </div>
            </div>
            <Link to="/login">Staff Login</Link>
          </nav>

          <div className="landing-nav-actions">
            <Link className="landing-library-btn" to="/library" aria-label="Open library">
              Open Library <ChevronRight size={16} />
            </Link>
          </div>
        </div>
      </header>

      <main className="landing-main">
        <section className="landing-hero" id="faculty">
          <div className="landing-hero-copy">
            <p className="landing-kicker">Faculty of Natural and Applied Sciences</p>
            <h1 className="landing-hero-title" aria-label="Welcome to the E-Library">
              <span className="landing-hero-title-text">Welcome to the E-Library</span>
            </h1>
            <p className="landing-hero-text">
              Discover curated resources for Computer Science, Information Systems, Data Science,
              Artificial Intelligence, and Cybersecurity in one flexible digital home.
            </p>
            <div className="landing-hero-actions">
              <Link className="landing-primary-cta" to="/library">
                Open Library
              </Link>
              <a className="landing-secondary-cta" href="#programs">Browse Programs</a>
            </div>
          </div>
        </section>

        <section className="landing-programs" id="programs">
          <div className="landing-section-head">
            <h2>Program Libraries</h2>
            <p>Choose a program below to enter its dedicated shelf.</p>
          </div>

          <div className="landing-program-grid" id="explore">
            {PROGRAMS.map((program) => {
              const Icon = program.icon;
              return (
                <Link key={program.slug} className="landing-program-card" to={`/library/category/${program.slug}`}>
                  <div className="landing-program-icon">
                    <Icon size={20} />
                  </div>
                  <h3>{program.name}</h3>
                  <p>{program.blurb}</p>
                  <span className="landing-program-link">
                    Open Program Library <ChevronRight size={14} />
                  </span>
                </Link>
              );
            })}
          </div>
        </section>
      </main>

      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <div className="landing-footer-brand">
            <div className="landing-footer-logo"><BookOpen size={18} /></div>
            <div>
              <h3>Veritas University E-Library</h3>
              <p>Academic digital library for Natural and Applied Sciences.</p>
            </div>
          </div>

          <div className="landing-footer-col">
            <h4>Faculty</h4>
            <a href="#faculty">Natural and Applied Sciences</a>
            <a href="#programs">Program Libraries</a>
            <Link to="/library">General Library</Link>
          </div>

          <div className="landing-footer-col">
            <h4>Programs</h4>
            <Link to="/library/category/computer-science">Computer Science</Link>
            <Link to="/library/category/information-systems">Information Systems</Link>
            <Link to="/library/category/data-science">Data Science</Link>
            <Link to="/library/category/artificial-intelligence">Artificial Intelligence</Link>
            <Link to="/library/category/cybersecurity">Cybersecurity</Link>
          </div>

          <div className="landing-footer-col">
            <h4>Quick Access</h4>
            <Link to="/library">Browse Library</Link>
            <Link to="/search">Search Books</Link>
            <Link to="/login">Staff Login</Link>
          </div>
        </div>

        <div className="landing-footer-bottom">
          <span>© 2026 Veritas University, Abuja. All rights reserved.</span>
        </div>
      </footer>
    </div>
  );
}
