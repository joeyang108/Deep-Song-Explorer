"""Article content extractor, quote finder, and studio context parser."""
import re
import urllib.parse
import urllib.request
from typing import List, Optional
from bs4 import BeautifulSoup
from .models import Article


def clean_raw_text(text: str) -> str:
    """Removes Wikipedia-style citations and normalizes spaces."""
    cleaned = re.sub(r"\[\s*(?:\d+|citation needed|[a-z]+)\s*\]", "", text)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned.strip()


def extract_quotes_from_text(text: str, max_quotes: int = 4) -> List[str]:
    """Extracts high-signal quotes related to the song and album creation."""
    quote_matches = re.findall(r'["“]([A-Z][^"”]{35,320})["”]', text)
    filtered = []
    
    intent_words = {
        "record", "recorded", "recording", "wrote", "written", "studio",
        "track", "tape", "song", "album", "lyric", "vocal", "drum",
        "bass", "sound", "producer", "idea", "accident", "session", "solo"
    }

    for q in quote_matches:
        q_clean = clean_raw_text(q).strip(' ,;:')
        q_lower = q_clean.lower()
        if any(w in q_lower for w in intent_words) and len(q_clean.split()) >= 6:
            filtered.append(q_clean)
            if len(filtered) >= max_quotes:
                break

    return filtered


def fetch_article_text(url: str, timeout: int = 8) -> Optional[str]:
    """Fetches a URL and extracts clean article body text."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            html = response.read().decode("utf-8", errors="ignore")
    except Exception:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # Strip non-content tags
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "noscript", "svg"]):
        tag.decompose()

    paragraphs = []
    for p in soup.find_all("p"):
        p_text = clean_raw_text(p.get_text(separator=" ", strip=True))
        if len(p_text) > 40 and not any(junk in p_text.lower() for junk in ["all rights reserved", "subscribe now", "cookie policy"]):
            paragraphs.append(p_text)

    if not paragraphs:
        return None

    return "\n\n".join(paragraphs)


def enrich_article(article: Article) -> Article:
    """Fetches full content for an article and populates quotes."""
    full_text = fetch_article_text(article.url)
    if full_text:
        article.full_text = full_text
        article.key_quotes = extract_quotes_from_text(full_text)
    return article
