"""Article content extractor, quote finder, and studio gear parser."""
import re
import urllib.request
import urllib.parse
from typing import List, Optional
from bs4 import BeautifulSoup
from .models import Article

# Gear keywords to scan for in text
GEAR_PATTERNS = [
    # Synthesizers & Keyboards
    r"\b(Fender\s+Rhodes|Rhodes\s+piano|Wurlitzer|Mellotron|Hammond\s+B-?3|Clavinet)\b",
    r"\b(Minimoog|Moog|Prophet-?5|Prophet-?6|Juno-?60|Juno-?106|Jupiter-?8|Yamaha\s+DX7|Fairlight|Synclavier)\b",
    # Microphones
    r"\b(Neumann\s+(?:U47|U87|U67|KM84|M49)|Shure\s+(?:SM57|SM58|SM7B)|AKG\s+(?:C414|C12)|Coles\s+4038|Electro-?Voice\s+RE20|Telefunken\s+ELA\s+M\s+251)\b",
    # Consoles, Tape Machines & Outboard
    r"\b(Neve(?:\s+\d{4})?|SSL(?:\s+\d{4})?|Solid\s+State\s+Logic|API\s+console|Trident\s+console)\b",
    r"\b(Studer\s+A800|Studer\s+A827|Ampex(?:\s+\d{3})?|3M\s+24-track|MCI\s+tape)\b",
    r"\b(LA-?2A|1176|Fairchild\s+670|Pultec(?:\s+EQP-1A)?|EMT\s+140\s+plate)\b",
    # Iconic Guitars / Amps / Drums
    r"\b(Fender\s+Stratocaster|Fender\s+Telecaster|Gibson\s+Les\s+Paul|Rickenbacker\s+360)\b",
    r"\b(Marshall\s+JCM800|Vox\s+AC30|Fender\s+Twin\s+Reverb)\b",
    r"\b(Ludwig\s+Supraphonic|Roland\s+TR-?808|Roland\s+TR-?909|LinnDrum|SP-?1200|Akai\s+MPC)\b"
]


def extract_gear_mentions(text: str) -> List[str]:
    """Finds audio equipment and instruments mentioned in the text."""
    found = set()
    for pattern in GEAR_PATTERNS:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        for m in matches:
            found.add(m.strip())
    return sorted(list(found))


def clean_raw_text(text: str) -> str:
    """Removes Wikipedia-style citations and normalizes spaces."""
    cleaned = re.sub(r"\[\s*(?:\d+|citation needed|[a-z]+)\s*\]", "", text)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned.strip()


def extract_quotes_from_text(text: str, max_quotes: int = 4) -> List[str]:
    """Extracts high-signal quotes related to the song creation."""
    # Look for quotes that start with an uppercase letter
    quote_matches = re.findall(r'["“]([A-Z][^"”]{35,320})["”]', text)
    filtered = []
    
    intent_words = {
        "record", "recorded", "recording", "wrote", "written", "studio",
        "track", "tape", "song", "lyric", "guitar", "vocal", "drum",
        "bass", "sound", "producer", "idea", "accident", "session", "solo"
    }

    for q in quote_matches:
        q_clean = clean_raw_text(q).strip(' ,;:')
        q_lower = q_clean.lower()
        # Must have at least one song/production intent word and look like a real sentence
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

    # Strip out non-content tags
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "noscript", "svg"]):
        tag.decompose()

    # Find paragraphs with real content
    paragraphs = []
    for p in soup.find_all("p"):
        p_text = clean_raw_text(p.get_text(separator=" ", strip=True))
        # Filter out cookie notices, short disclaimers, or empty elements
        if len(p_text) > 40 and not any(junk in p_text.lower() for junk in ["all rights reserved", "subscribe now", "cookie policy"]):
            paragraphs.append(p_text)

    if not paragraphs:
        return None

    return "\n\n".join(paragraphs)


def enrich_article(article: Article) -> Article:
    """Fetches full content for an article and populates quotes and gear."""
    full_text = fetch_article_text(article.url)
    if full_text:
        article.full_text = full_text
        article.key_quotes = extract_quotes_from_text(full_text)
        article.gear_mentioned = extract_gear_mentions(full_text)
    return article
