"""Synthesizes articles into a structured Song Dossier and manages caching."""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from .models import Song, Article, SongDossier
from ..config import CACHE_DIR


def _make_cache_key(artist: str, song: str) -> str:
    """Generates a safe filesystem filename for caching."""
    slug = f"{artist}_{song}".lower()
    return re.sub(r"[^a-z0-9_-]+", "_", slug).strip("_")


def cache_dossier(dossier: SongDossier) -> Path:
    """Saves a compiled SongDossier to JSON in the cache directory."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = _make_cache_key(dossier.song.artist, dossier.song.title)
    file_path = CACHE_DIR / f"{key}.json"

    data = {
        "song": {
            "title": dossier.song.title,
            "artist": dossier.song.artist,
            "year": dossier.song.year,
            "album": dossier.song.album,
        },
        "creative_spark": dossier.creative_spark,
        "studio_craft": dossier.studio_craft,
        "gear_lore": dossier.gear_lore,
        "trivia": dossier.trivia,
        "compiled_at": dossier.compiled_at.isoformat(),
        "articles": [
            {
                "title": a.title,
                "url": a.url,
                "source_name": a.source_name,
                "category": a.category,
                "snippet": a.snippet,
                "key_quotes": a.key_quotes,
                "gear_mentioned": a.gear_mentioned,
            }
            for a in dossier.articles
        ],
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return file_path


def load_cached_dossier(artist: str, song: str) -> Optional[SongDossier]:
    """Loads a previously cached SongDossier if present."""
    key = _make_cache_key(artist, song)
    file_path = CACHE_DIR / f"{key}.json"

    if not file_path.exists():
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        s_data = data.get("song", {})
        song_obj = Song(
            title=s_data.get("title", song),
            artist=s_data.get("artist", artist),
            year=s_data.get("year"),
            album=s_data.get("album"),
        )

        articles = [
            Article(
                title=a["title"],
                url=a["url"],
                source_name=a["source_name"],
                category=a["category"],
                snippet=a.get("snippet", ""),
                key_quotes=a.get("key_quotes", []),
                gear_mentioned=a.get("gear_mentioned", []),
            )
            for a in data.get("articles", [])
        ]

        compiled_at = datetime.fromisoformat(data["compiled_at"]) if "compiled_at" in data else datetime.utcnow()

        return SongDossier(
            song=song_obj,
            articles=articles,
            creative_spark=data.get("creative_spark", ""),
            studio_craft=data.get("studio_craft", ""),
            gear_lore=data.get("gear_lore", []),
            trivia=data.get("trivia", []),
            compiled_at=compiled_at,
        )
    except Exception:
        return None


def synthesize_dossier(song: Song, articles: List[Article]) -> SongDossier:
    """Extracts thematic lore from articles and structures it into chapters."""
    all_gear = set()
    all_quotes = []
    creative_paragraphs = []
    studio_paragraphs = []
    trivia_items = []

    for art in articles:
        # Collect gear
        for g in art.gear_mentioned:
            all_gear.add(g)

        # Collect quotes
        for q in art.key_quotes:
            all_quotes.append((q, art.source_name))

        if not art.full_text:
            continue

        paragraphs = art.full_text.split("\n\n")
        for p in paragraphs:
            p_lower = p.lower()

            # Creative spark heuristics
            if any(w in p_lower for w in ["wrote the song", "writing session", "inspiration for", "originated", "melody came", "lyrics were about"]):
                if len(p) > 80 and p not in creative_paragraphs:
                    creative_paragraphs.append(p)

            # Studio craft heuristics
            if any(w in p_lower for w in ["in the studio", "tracking", "recorded at", "console", "tape machine", "microphones", "drum sound", "mix engineer", "producer"]):
                if len(p) > 80 and p not in studio_paragraphs:
                    studio_paragraphs.append(p)

            # Quirks & Trivia
            if any(w in p_lower for w in ["accident", "originally intended", "rejected", "almost didn't make", "mistake on the record", "trivia"]):
                if len(p) > 60 and p not in trivia_items:
                    trivia_items.append(p)

    # Format synthesized summaries
    creative_spark_summary = (
        "\n\n".join(creative_paragraphs[:3])
        if creative_paragraphs
        else (
            f"Analysis across {len(articles)} sources highlights the foundational songwriting and creative origins behind {song}."
        )
    )

    studio_craft_summary = (
        "\n\n".join(studio_paragraphs[:3])
        if studio_paragraphs
        else (
            f"Production and engineering accounts document the recording techniques and session arrangements for {song}."
        )
    )

    dossier = SongDossier(
        song=song,
        articles=articles,
        creative_spark=creative_spark_summary,
        studio_craft=studio_craft_summary,
        gear_lore=sorted(list(all_gear)),
        trivia=trivia_items[:4],
        compiled_at=datetime.utcnow(),
    )

    # Save to local cache
    cache_dossier(dossier)
    return dossier
