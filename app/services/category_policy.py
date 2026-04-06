from __future__ import annotations

from app.config import ALLOWED_CATEGORY_SLUGS

SLUG_TO_NAME = {
    "cybersecurity": "Cybersecurity",
    "data-science": "Data Science",
    "artificial-intelligence": "Artificial Intelligence",
    "information-systems": "Information Systems",
    "computer-science": "Computer Science",
}

ALLOWED_CATEGORY_NAMES = tuple(SLUG_TO_NAME[slug] for slug in ALLOWED_CATEGORY_SLUGS if slug in SLUG_TO_NAME)

_ALIAS_TO_SLUG = {
    "cybersecurity": "cybersecurity",
    "cyber security": "cybersecurity",
    "cyber-security": "cybersecurity",
    "data science": "data-science",
    "data-science": "data-science",
    "datascience": "data-science",
    "artificial intelligence": "artificial-intelligence",
    "artificial-intelligence": "artificial-intelligence",
    "ai": "artificial-intelligence",
    "a.i": "artificial-intelligence",
    "information systems": "information-systems",
    "information-systems": "information-systems",
    "information system": "information-systems",
    "infosystems": "information-systems",
    "is": "information-systems",
    "computer science": "computer-science",
    "computer-science": "computer-science",
    "cs": "computer-science",
    "c.s": "computer-science",
    "computing": "computer-science",
}


def normalize_category(value: str | None) -> str | None:
    if not value:
        return None
    key = str(value).strip().lower().replace("_", " ")
    slug = _ALIAS_TO_SLUG.get(key)
    if not slug:
        key2 = key.replace(" ", "-")
        slug = _ALIAS_TO_SLUG.get(key2)
    if not slug:
        return None
    return SLUG_TO_NAME.get(slug)


def slug_from_category(value: str | None) -> str | None:
    normalized = normalize_category(value)
    if not normalized:
        return None
    for slug, name in SLUG_TO_NAME.items():
        if name == normalized:
            return slug
    return None


def allowed_categories_payload() -> list[dict]:
    return [
        {
            "id": slug,
            "name": name,
            "slug": slug,
            "description": "",
        }
        for slug, name in SLUG_TO_NAME.items()
    ]
