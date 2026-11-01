"""Targeted search engine for music making-of articles, studio lore, and album retrospectives."""
import re
import urllib.parse
from typing import Dict, List, Optional, Set, Tuple
from .models import Article
from ..config import CURATED_SOURCES

# Domains to explicitly discard (low signal, lyrics, streaming, chords)
JUNK_DOMAINS = {
    "spotify.com", "apple.com", "youtube.com", "youtu.be",
    "soundcloud.com", "pandora.com", "tidal.com", "deezer.com",
    "azlyrics.com", "lyrics.com", "genius.com/albums",
    "ultimate-guitar.com", "chordie.com", "e-chords.com", "tabs.ultimate-guitar.com",
    "tiktok.com", "instagram.com", "facebook.com", "twitter.com", "x.com",
    "amazon.com", "ebay.com", "discogs.com/sell"
}


def get_curated_domain_map() -> Dict[str, Dict[str, str]]:
    """Maps domain roots to their display name and category."""
    mapping = {}
    for src in CURATED_SOURCES:
        mapping[src["domain"]] = {
            "name": src["name"],
            "category": src["category"]
        }
    return mapping


def generate_song_queries(artist: str, song: str) -> List[str]:
    """Generates natural, high-intent search queries for a specific song."""
    clean_artist = artist.strip().replace('"', '')
    clean_song = song.strip().replace('"', '')
    
    return [
        f'"{clean_artist}" "{clean_song}" making of',
        f'"{clean_artist}" "{clean_song}" in the studio recording',
        f'"{clean_artist}" "{clean_song}" oral history interview',
        f'"{clean_artist}" "{clean_song}" Sound On Sound',
        f'"{clean_artist}" "{clean_song}" behind the song',
        f'"{clean_artist}" "{clean_song}" Song Exploder'
    ]


def generate_album_queries(artist: str, album: str) -> List[str]:
    """Generates high-intent search queries for album-wide production lore."""
    clean_artist = artist.strip().replace('"', '')
    clean_album = album.strip().replace('"', '')
    
    return [
        f'"{clean_artist}" "{clean_album}" in the studio recording',
        f'"{clean_artist}" "{clean_album}" making of',
        f'"{clean_artist}" "{clean_album}" Sound On Sound',
        f'"{clean_artist}" "{clean_album}" Tape Op interview',
        f'"{clean_artist}" "{clean_album}" retrospective oral history'
    ]


def _categorize_url(url: str, is_album: bool = False) -> Dict[str, str]:
    """Identifies the publication name and category from a URL."""
    domain_map = get_curated_domain_map()
    parsed = urllib.parse.urlparse(url)
    netloc = parsed.netloc.lower()

    for domain, info in domain_map.items():
        if domain in netloc:
            cat = "album_retrospective" if is_album else info["category"]
            return {"name": info["name"], "category": cat}

    default_cat = "album_retrospective" if is_album else "deep_dive"
    if "wikipedia.org" in netloc:
        return {"name": "Wikipedia (Studio & Lore)", "category": "encyclopedic_lore"}
    if any(k in netloc for k in ["theguardian", "rollingstone", "stereogum", "billboard", "npr", "faroutmagazine", "spin"]):
        return {"name": netloc.replace("www.", ""), "category": "album_retrospective" if is_album else "oral_history"}
    if any(k in netloc for k in ["gearnews", "musictech", "soundonsound", "tapeop", "prosoundnetwork", "reverb"]):
        return {"name": netloc.replace("www.", ""), "category": "album_studio" if is_album else "studio_craft"}

    return {"name": netloc.replace("www.", ""), "category": default_cat}


def _is_junk_url(url: str) -> bool:
    """Checks if the URL matches junk/low-signal patterns."""
    url_lower = url.lower()
    for junk in JUNK_DOMAINS:
        if junk in url_lower:
            return True
    return False


def execute_ddg_search(query: str, max_results: int = 4) -> List[Dict[str, str]]:
    """Executes a search query using ddgs or fallback HTTP."""
    results = []

    # 1. Try ddgs / duckduckgo_search library
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
            
        with DDGS() as ddg:
            raw_results = list(ddg.text(query, max_results=max_results))
            for r in raw_results:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", "") or r.get("link", ""),
                    "snippet": r.get("body", "") or r.get("snippet", "")
                })
        return results
    except Exception:
        pass

    # 2. Fallback: direct HTTP via DuckDuckGo HTML
    try:
        import urllib.request
        from bs4 import BeautifulSoup

        url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
            }
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            html = response.read().decode("utf-8", errors="ignore")
            soup = BeautifulSoup(html, "html.parser")
            for result_div in soup.find_all("div", class_="result", limit=max_results):
                title_a = result_div.find("a", class_="result__a")
                snippet_tag = result_div.find("a", class_="result__snippet")
                if title_a and title_a.get("href"):
                    raw_href = title_a["href"]
                    match = re.search(r"uddg=([^&]+)", raw_href)
                    final_url = urllib.parse.unquote(match.group(1)) if match else raw_href
                    results.append({
                        "title": title_a.get_text(strip=True),
                        "url": final_url,
                        "snippet": snippet_tag.get_text(strip=True) if snippet_tag else ""
                    })
    except Exception:
        pass

    return results


def search_dual_tier(
    artist: str,
    song: str,
    album: Optional[str] = None,
    max_song_articles: int = 4,
    max_album_articles: int = 4
) -> Tuple[List[Article], List[Article]]:
    """Always searches for BOTH Song Articles AND Album Retrospectives.
    
    Returns:
        (song_articles, album_articles)
    """
    seen_urls: Set[str] = set()
    song_articles: List[Article] = []
    album_articles: List[Article] = []

    # 1. Collect Song-Specific Articles
    song_queries = generate_song_queries(artist, song)
    for q in song_queries:
        items = execute_ddg_search(q, max_results=3)
        for it in items:
            url = it["url"]
            if not url or url in seen_urls or _is_junk_url(url):
                continue
            seen_urls.add(url)
            cat_info = _categorize_url(url, is_album=False)
            song_articles.append(Article(
                title=it["title"],
                url=url,
                source_name=cat_info["name"],
                category=cat_info["category"],
                snippet=it["snippet"],
                is_album_level=False,
            ))
            if len(song_articles) >= max_song_articles:
                break
        if len(song_articles) >= max_song_articles:
            break

    # 2. Collect Album-Specific Articles
    target_album = album or song
    album_queries = generate_album_queries(artist, target_album)
    for q in album_queries:
        items = execute_ddg_search(q, max_results=3)
        for it in items:
            url = it["url"]
            if not url or url in seen_urls or _is_junk_url(url):
                continue
            seen_urls.add(url)
            cat_info = _categorize_url(url, is_album=True)
            album_articles.append(Article(
                title=it["title"],
                url=url,
                source_name=cat_info["name"],
                category=cat_info["category"],
                snippet=it["snippet"],
                is_album_level=True,
            ))
            if len(album_articles) >= max_album_articles:
                break
        if len(album_articles) >= max_album_articles:
            break

    return song_articles, album_articles


def search_articles(artist: str, song: str, max_total: int = 7) -> List[Article]:
    """Legacy helper for backward compatibility."""
    song_arts, alb_arts = search_dual_tier(artist, song, max_song_articles=4, max_album_articles=3)
    return song_arts + alb_arts
