import httpx
import time
from pathlib import Path
from urllib.parse import quote
from sqlalchemy.orm import Session
from app.models.book import Book, BookType
from app.models.category import Category
from app.models.download import Download
from app.services import internet_archive

# ──────────────────────────────────────────────────────────────
# Only 3 categories: Cybersecurity, Data Science, AI
# Curated search queries + subject filters for strict matching
# ──────────────────────────────────────────────────────────────

TARGET_BOOKS_PER_CATEGORY = 10

ARCHIVE_CATEGORY_QUERIES = {
    "cybersecurity": [
        "cybersecurity",
        "network security",
        "information security",
        "ethical hacking",
        "cryptography",
    ],
    "data-science": [
        "data science",
        "machine learning",
        "statistics",
        "data analysis",
        "big data",
    ],
    "artificial-intelligence": [
        "artificial intelligence",
        "deep learning",
        "neural networks",
        "machine learning",
        "natural language processing",
    ],
}

ARCHIVE_STRICT_KEYWORDS = {
    "cybersecurity": {
        "cybersecurity",
        "network security",
        "information security",
        "ethical hacking",
        "penetration testing",
        "cryptography",
        "malware",
        "firewall",
        "intrusion",
        "vulnerability",
        "threat",
        "risk",
        "forensic",
        "security+",
    },
    "data-science": {
        "data science",
        "machine learning",
        "statistical learning",
        "statistics",
        "data analysis",
        "data mining",
        "predictive analytics",
        "regression",
        "clustering",
        "probabilistic",
        "pattern recognition",
        "big data",
    },
    "artificial-intelligence": {
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "neural network",
        "neural networks",
        "reinforcement learning",
        "natural language processing",
        "computer vision",
        "multiagent",
        "intelligent systems",
    },
}

ARCHIVE_REJECT_KEYWORDS = {
    "cybersecurity": {
        "cooking",
        "recipe",
        "romance",
        "fiction",
        "poetry",
        "gardening",
        "knitting",
        "novel",
        "journal",
        "journals",
        "article",
        "articles",
        "proceedings",
        "transactions",
        "conference",
        "symposium",
        "workshop",
        "bulletin",
        "newsletter",
        "technical report",
        "annual report",
        "paper",
        "papers",
        "review",
        "reviews",
        "bible",
        "prayer",
        "astrology",
        "zodiac",
        "real estate",
        "stock market",
        "air traffic",
        "coast guard",
    },
    "data-science": {
        "cooking",
        "recipe",
        "romance",
        "fiction",
        "poetry",
        "gardening",
        "knitting",
        "novel",
        "journal",
        "journals",
        "article",
        "articles",
        "proceedings",
        "transactions",
        "conference",
        "symposium",
        "workshop",
        "bulletin",
        "newsletter",
        "technical report",
        "annual report",
        "paper",
        "papers",
        "review",
        "reviews",
        "bible",
        "prayer",
        "astrology",
        "zodiac",
        "real estate",
        "stock market",
        "air traffic",
        "coast guard",
        "computer science",
    },
    "artificial-intelligence": {
        "cooking",
        "recipe",
        "romance",
        "fiction",
        "poetry",
        "gardening",
        "knitting",
        "novel",
        "journal",
        "journals",
        "article",
        "articles",
        "proceedings",
        "transactions",
        "conference",
        "symposium",
        "workshop",
        "bulletin",
        "newsletter",
        "technical report",
        "annual report",
        "paper",
        "papers",
        "review",
        "reviews",
        "bible",
        "prayer",
        "astrology",
        "zodiac",
        "real estate",
        "stock market",
        "air traffic",
        "coast guard",
    },
}

CATEGORY_QUERIES = {
    "cybersecurity": [
        ("network security fundamentals", "computer_security"),
        ("ethical hacking penetration testing", "computer_security"),
        ("information security management", "computer_security"),
        ("cybersecurity defense", "computer_security"),
        ("cryptography computer", "cryptography"),
    ],
    "data-science": [
        ("data science python", "data_analysis"),
        ("machine learning statistical", "machine_learning"),
        ("statistics data analysis", "statistics"),
        ("big data analytics", "data_analysis"),
        ("data mining techniques", "data_analysis"),
    ],
    "artificial-intelligence": [
        ("artificial intelligence modern approach", "artificial_intelligence"),
        ("deep learning neural network", "artificial_intelligence"),
        ("machine learning textbook", "machine_learning"),
        ("natural language processing", "artificial_intelligence"),
        ("reinforcement learning", "artificial_intelligence"),
    ],
}

# Must contain at least ONE tech keyword
TECH_KEYWORDS = {
    "computer", "programming", "software", "algorithm", "data",
    "network", "security", "system", "database", "sql",
    "machine learning", "artificial intelligence", "deep learning",
    "neural", "python", "java", "web", "internet", "protocol",
    "cyber", "hacking", "cryptography", "encryption",
    "cloud", "distributed", "architecture", "testing",
    "statistics", "analytics", "mining", "modeling",
    "intelligence", "learning", "science", "information",
    "pattern", "recognition", "classification", "regression",
    "natural language", "reinforcement", "tensorflow", "keras",
    "penetration", "malware", "forensic", "firewall",
    "intrusion", "vulnerability", "threat", "risk",
    "big data", "hadoop", "spark", "visualization",
}

# Hard-reject
REJECT_KEYWORDS = {
    "romance", "cooking", "recipe", "diet", "pregnancy", "bible",
    "prayer", "astrology", "zodiac", "coloring book", "sudoku",
    "crossword", "knitting", "gardening", "financial planning",
    "real estate", "stock market", "forex", "yoga", "meditation",
    "novel", "fiction", "poetry", "poems", "fairy tale",
    "ender's game", "arabian", "social security",
    "food safety", "coast guard", "air traffic", "tax systems",
}


def seed_books_from_open_library(db: Session):
    """Fetch 50 strictly relevant books per category with covers."""
    existing_count = db.query(Book).count()
    if existing_count > 0:
        return

    print("[Seed] Fetching books from Open Library (3 categories, 50 each)...")

    categories = db.query(Category).all()
    for cat in categories:
        queries = CATEGORY_QUERIES.get(cat.slug, [])
        if not queries:
            continue

        collected = []
        seen_keys = set()

        for search_query, subject_filter in queries:
            if len(collected) >= 50:
                break
            try:
                books = _search_strict(search_query, subject_filter, limit=50)
                for b in books:
                    if b["api_id"] in seen_keys:
                        continue
                    if not _is_relevant(b["title"]):
                        continue
                    seen_keys.add(b["api_id"])
                    collected.append(b)
                    if len(collected) >= 50:
                        break
                time.sleep(0.3)
            except Exception as e:
                print(f"[Seed]   query '{search_query}' error: {e}")

        # If we didn't get 50, do a second pass with looser limits
        if len(collected) < 50:
            for search_query, subject_filter in queries:
                if len(collected) >= 50:
                    break
                try:
                    books = _search_strict(search_query, subject_filter, limit=50)
                    for b in books:
                        if b["api_id"] in seen_keys:
                            continue
                        if not _is_relevant(b["title"]):
                            continue
                        seen_keys.add(b["api_id"])
                        collected.append(b)
                        if len(collected) >= 50:
                            break
                except Exception:
                    pass

        # Now fetch descriptions for each book
        for b in collected:
            if not b.get("description"):
                try:
                    desc = fetch_book_description(b["api_id"])
                    b["description"] = desc
                    time.sleep(0.15)
                except Exception:
                    pass

        # Persist
        for book_data in collected:
            exists = db.query(Book).filter(Book.api_id == book_data["api_id"]).first()
            if exists:
                continue
            cover_image = book_data.get("cover_image", "")
            if not cover_image:
                cover_image = _make_local_cover(book_data["title"], cat.slug)
            book = Book(
                title=book_data["title"],
                author=book_data["author"],
                description=book_data.get("description", ""),
                category_id=cat.id,
                cover_image=cover_image,
                book_type=BookType.external,
                view_link=book_data.get("view_link", ""),
                source="open_library",
                api_id=book_data["api_id"],
                added_by=1,
                download_count=0,
            )
            db.add(book)

        db.commit()
        print(f"[Seed] ✓ {cat.name}: {len(collected)} books imported")

    from app.services.book_service import get_allowed_book_count
    if get_allowed_book_count(db) == 0:
        _seed_local_fallback_books(db)


async def seed_books_from_internet_archive(db: Session, target_per_category: int = TARGET_BOOKS_PER_CATEGORY):
    """Top up archive-backed books so each allowed category has at least 10 entries."""
    print(f"[Seed] Ensuring at least {target_per_category} Internet Archive books per category...")

    removed = _purge_off_topic_archive_books(db)
    if removed:
        print(f"[Seed] Removed {removed} off-topic archive books before reseeding")

    categories = db.query(Category).all()
    for cat in categories:
        queries = ARCHIVE_CATEGORY_QUERIES.get(cat.slug, [])
        if not queries:
            continue

        existing_count = (
            db.query(Book)
            .filter(
                Book.category_id == cat.id,
                Book.book_type == BookType.archive,
                Book.source == "Internet Archive",
            )
            .count()
        )
        needed = max(0, target_per_category - existing_count)
        if needed == 0:
            print(f"[Seed] ✓ {cat.name}: already has {existing_count} archive books")
            continue

        collected = await _collect_archive_books(cat.slug, queries, needed)

        for book_data in collected:
            archive_id = book_data.get("archive_id", "").strip()
            if not archive_id:
                continue

            exists = (
                db.query(Book)
                .filter(Book.archive_id == archive_id, Book.book_type == BookType.archive)
                .first()
            )
            if exists:
                continue

            db.add(Book(
                title=book_data.get("title", "Unknown Title"),
                author=book_data.get("author", "Unknown Author"),
                description=book_data.get("description", ""),
                category_id=cat.id,
                cover_image=book_data.get("cover_image", ""),
                book_type=BookType.archive,
                preview_link=book_data.get("preview_link", ""),
                view_link=book_data.get("download_link", ""),
                download_link=book_data.get("download_link", ""),
                source="Internet Archive",
                archive_id=archive_id,
                api_id=archive_id,
                added_by=1,
                download_count=0,
            ))

        db.commit()

        final_count = (
            db.query(Book)
            .filter(
                Book.category_id == cat.id,
                Book.book_type == BookType.archive,
                Book.source == "Internet Archive",
            )
            .count()
        )
        print(f"[Seed] ✓ {cat.name}: {final_count} archive books available")


async def _collect_archive_books(category_slug: str, queries: list[str], target: int) -> list[dict]:
    collected: list[dict] = []
    seen_ids: set[str] = set()

    for query in queries:
        if len(collected) >= target:
            break

        try:
            search_results = await internet_archive.search_books(query=query, limit=25)
        except Exception as exc:
            print(f"[Seed]   archive query '{query}' error: {exc}")
            continue

        for candidate in search_results:
            if len(collected) >= target:
                break

            archive_id = str(candidate.get("archive_id", "")).strip()
            if not archive_id or archive_id in seen_ids:
                continue
            seen_ids.add(archive_id)

            try:
                details = await internet_archive.get_book_details(archive_id)
            except Exception:
                continue

            if not details or not details.get("download_link"):
                continue

            if not _is_relevant_for_category(category_slug, details.get("title", ""), details.get("description", "")):
                continue

            collected.append(details)

    return collected


def _purge_off_topic_archive_books(db: Session) -> int:
    removed = 0
    books = (
        db.query(Book)
        .filter(Book.book_type == BookType.archive, Book.source == "Internet Archive")
        .all()
    )

    for book in books:
        category = book.category.slug if book.category else ""
        if category and _is_relevant_for_category(category, book.title, book.description or ""):
            continue
        db.query(Download).filter(Download.book_id == book.id).delete(synchronize_session=False)
        db.delete(book)
        removed += 1

    if removed:
        db.commit()

    return removed


def _seed_local_fallback_books(db: Session):
    """Seed a small offline catalog if Open Library is unavailable."""
    print("[Seed] Open Library seed returned no books; using local fallback set.")

    categories = {
        "cybersecurity": [
            "Security+ Guide to Networking Security Fundamentals",
            "Network Security Fundamentals",
            "Hacking for Dummies",
            "The basics of hacking and penetration testing",
            "CompTIA Security+ Guide to Network Security Fundamentals",
            "Cryptography and Network Security",
            "Practical Malware Analysis",
            "Cybersecurity and Cyberwar",
            "Applied Cryptography",
            "Computer Security: Art and Science",
        ],
        "data-science": [
            "Statistical Learning Using Neural Networks",
            "Pattern Recognition and Machine Learning",
            "Python machine learning",
            "Computational Statistics and Machine Learning",
            "Statistical data analysis",
            "An Introduction to Statistical Learning",
            "Data Mining: Practical Machine Learning Tools and Techniques",
            "Machine Learning: A Probabilistic Perspective",
            "Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow",
            "Data Science from Scratch",
        ],
        "artificial-intelligence": [
            "Artificial intelligence",
            "Distributed Artificial Intelligence",
            "Multiagent Systems",
            "Intelligent Systems",
            "Hands-On Neural Networks with Keras",
            "Artificial Intelligence: A Modern Approach",
            "Deep Learning",
            "Neural Networks and Deep Learning",
            "Reinforcement Learning: An Introduction",
            "Machine Learning",
        ],
    }

    category_rows = db.query(Category).filter(Category.slug.in_(categories.keys())).all()
    for category in category_rows:
        for index, title in enumerate(categories.get(category.slug, []), start=1):
            exists = db.query(Book).filter(Book.title == title, Book.category_id == category.id).first()
            if exists:
                continue
            db.add(Book(
                title=title,
                author="Curated academic collection",
                description=f"Curated {category.name.lower()} title seeded locally when Open Library is unavailable.",
                category_id=category.id,
                cover_image=_make_local_cover(title, category.slug),
                book_type=BookType.external,
                view_link="",
                source="local_seed",
                api_id=f"local-{category.slug}-{index}",
                added_by=1,
                download_count=0,
            ))

    db.commit()
    print(f"[Seed] ✓ Local fallback seed inserted {db.query(Book).count()} books")


def _make_local_cover(title: str, category_slug: str) -> str:
    """Generate a fast, local SVG cover so cards render immediately."""
    theme = {
        "cybersecurity": ("#0f766e", "#134e4a"),
        "data-science": ("#2563eb", "#1d4ed8"),
        "artificial-intelligence": ("#7c3aed", "#5b21b6"),
    }
    start, end = theme.get(category_slug, ("#374151", "#111827"))
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    words = safe_title.split()
    if len(words) > 6:
        safe_title = " ".join(words[:6]) + "..."

    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 600'>
      <defs>
        <linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>
          <stop offset='0%' stop-color='{start}'/>
          <stop offset='100%' stop-color='{end}'/>
        </linearGradient>
      </defs>
      <rect width='400' height='600' rx='28' fill='url(#g)'/>
      <circle cx='320' cy='92' r='66' fill='rgba(255,255,255,0.10)'/>
      <circle cx='88' cy='512' r='92' fill='rgba(255,255,255,0.08)'/>
      <text x='40' y='86' fill='white' font-family='Inter, Arial, sans-serif' font-size='28' font-weight='700'>E-Library</text>
      <text x='40' y='138' fill='rgba(255,255,255,0.85)' font-family='Inter, Arial, sans-serif' font-size='18' font-weight='500'>{category_slug.replace('-', ' ').title()}</text>
      <text x='40' y='270' fill='white' font-family='Georgia, serif' font-size='34' font-weight='700'>{safe_title}</text>
    </svg>"""
    return f"data:image/svg+xml;charset=utf-8,{quote(svg)}"


def _search_strict(query: str, subject: str, limit: int = 50) -> list[dict]:
    """Search Open Library with query + subject filter."""
    url = "https://openlibrary.org/search.json"
    params = {
        "q": query,
        "subject": subject,
        "limit": min(limit, 100),
        "fields": "key,title,author_name,cover_i,first_sentence,subject",
        "language": "eng",
    }

    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, params=params)
        if resp.status_code != 200:
            return []
        data = resp.json()

    results = []
    for doc in data.get("docs", []):
        cover_id = doc.get("cover_i")
        # Use -M (medium, 180px) for fast card loading, -L for detail page
        cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else ""
        work_key = doc.get("key", "")
        authors = doc.get("author_name", ["Unknown Author"])

        description = ""
        first_sentence = doc.get("first_sentence", [])
        if isinstance(first_sentence, list) and first_sentence:
            description = first_sentence[0]
        elif isinstance(first_sentence, str):
            description = first_sentence

        results.append({
            "api_id": work_key,
            "title": doc.get("title", "Unknown Title"),
            "author": ", ".join(authors[:2]),
            "description": description,
            "cover_image": cover_url,
            "view_link": f"https://openlibrary.org{work_key}",
        })

    return results


def _is_relevant(title: str) -> bool:
    """Check tech keyword whitelist / reject blacklist."""
    lower = title.lower()
    for kw in {
        "journal",
        "journals",
        "article",
        "articles",
        "proceedings",
        "transactions",
        "conference",
        "symposium",
        "workshop",
        "bulletin",
        "newsletter",
        "technical report",
        "annual report",
        "paper",
        "papers",
        "review",
        "reviews",
    }:
        if kw in lower:
            return False
    for kw in REJECT_KEYWORDS:
        if kw in lower:
            return False
    for kw in TECH_KEYWORDS:
        if kw in lower:
            return True
    return False


def _is_relevant_for_category(category_slug: str, title: str, description: str = "") -> bool:
    text = f"{title} {description}".lower()
    for kw in ARCHIVE_REJECT_KEYWORDS.get(category_slug, set()):
        if kw in text:
            return False

    keywords = ARCHIVE_STRICT_KEYWORDS.get(category_slug, set())
    return any(keyword in text for keyword in keywords)


def fetch_book_description(work_key: str) -> str:
    """Fetch description for a work from Open Library."""
    url = f"https://openlibrary.org{work_key}.json"
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url)
            if resp.status_code != 200:
                return ""
            data = resp.json()
            desc = data.get("description", "")
            if isinstance(desc, dict):
                return desc.get("value", "")
            return desc or ""
    except Exception:
        return ""
