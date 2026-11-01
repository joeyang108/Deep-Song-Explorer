"""Synthesizes articles into a structured Song Dossier and manages caching."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from .models import (
    Song, Article, DiscographyEntry, ProducerPedigree,
    StudioHeritage, SongDossier
)
from .studios import detect_studio_facility
from .producers import resolve_producers_and_collaborators
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

    # Serialize studio sanctuary
    studio_dict = None
    if dossier.studio_sanctuary:
        s = dossier.studio_sanctuary
        studio_dict = {
            "facility_name": s.facility_name,
            "location": s.location,
            "why_chosen": s.why_chosen,
            "prior_landmarks": s.prior_landmarks,
            "contemporary_peers": s.contemporary_peers,
            "collaborators": s.collaborators,
            "lead_engineer": s.lead_engineer,
            "producers": [
                {
                    "name": p.name,
                    "role": p.role,
                    "with_queried_artist": p.with_queried_artist,
                    "with_related_artists": p.with_related_artists,
                }
                for p in s.producers
            ],
        }

    data = {
        "song": {
            "title": dossier.song.title,
            "artist": dossier.song.artist,
            "year": dossier.song.year,
            "album": dossier.song.album,
            "original_query": dossier.song.original_query,
            "musicbrainz_id": dossier.song.musicbrainz_id,
        },
        "song_articles_count": dossier.song_articles_count,
        "album_articles_count": dossier.album_articles_count,
        "creative_spark": dossier.creative_spark,
        "album_lore": dossier.album_lore,
        "discography_summary": dossier.discography_summary,
        "discography_context": [
            {
                "title": d.title if hasattr(d, "title") else d["title"],
                "release_date": d.release_date if hasattr(d, "release_date") else d["release_date"],
                "allmusic_rating": d.allmusic_rating if hasattr(d, "allmusic_rating") else d["allmusic_rating"],
                "relationship": d.relationship if hasattr(d, "relationship") else d["relationship"],
                "is_current": d.is_current if hasattr(d, "is_current") else d.get("is_current", False),
            }
            for d in dossier.discography_context
        ],
        "studio_sanctuary": studio_dict,
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
                "is_album_level": a.is_album_level,
            }
            for a in dossier.articles
        ],
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return file_path


def load_cached_dossier(artist: str, song: str) -> Optional[SongDossier]:
    """Loads a previously cached SongDossier if present with backward compatibility."""
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
            original_query=s_data.get("original_query"),
            musicbrainz_id=s_data.get("musicbrainz_id"),
        )

        articles = [
            Article(
                title=a["title"],
                url=a["url"],
                source_name=a["source_name"],
                category=a["category"],
                snippet=a.get("snippet", ""),
                key_quotes=a.get("key_quotes", []),
                is_album_level=a.get("is_album_level", False),
            )
            for a in data.get("articles", [])
        ]

        # Discography
        discography = [
            DiscographyEntry(
                title=d["title"],
                release_date=d["release_date"],
                allmusic_rating=d["allmusic_rating"],
                relationship=d["relationship"],
                is_current=d.get("is_current", False),
            )
            for d in data.get("discography_context", [])
        ]

        # Studio Sanctuary
        studio_sanctuary = None
        s_raw = data.get("studio_sanctuary")
        if s_raw:
            producers = [
                ProducerPedigree(
                    name=p["name"],
                    role=p["role"],
                    with_queried_artist=p.get("with_queried_artist", []),
                    with_related_artists=p.get("with_related_artists", []),
                )
                for p in s_raw.get("producers", [])
            ]
            studio_sanctuary = StudioHeritage(
                facility_name=s_raw.get("facility_name", ""),
                location=s_raw.get("location", ""),
                why_chosen=s_raw.get("why_chosen", ""),
                prior_landmarks=s_raw.get("prior_landmarks", []),
                contemporary_peers=s_raw.get("contemporary_peers", []),
                producers=producers,
                collaborators=s_raw.get("collaborators", []),
                lead_engineer=s_raw.get("lead_engineer"),
            )

        compiled_at = (
            datetime.fromisoformat(data["compiled_at"])
            if "compiled_at" in data
            else datetime.now(timezone.utc)
        )

        # Compute counts if missing in older cache
        song_count = data.get("song_articles_count", sum(1 for a in articles if not a.is_album_level))
        alb_count = data.get("album_articles_count", sum(1 for a in articles if a.is_album_level))

        return SongDossier(
            song=song_obj,
            song_articles_count=song_count,
            album_articles_count=alb_count,
            articles=articles,
            creative_spark=data.get("creative_spark", ""),
            album_lore=data.get("album_lore", ""),
            discography_context=discography,
            discography_summary=data.get("discography_summary", ""),
            studio_sanctuary=studio_sanctuary,
            trivia=data.get("trivia", []),
            compiled_at=compiled_at,
        )
    except Exception:
        return None


def synthesize_dossier(
    song: Song,
    song_articles: List[Article],
    album_articles: List[Article],
    discography_context: List[DiscographyEntry] = None,
    discography_summary: str = ""
) -> SongDossier:
    """Extracts thematic lore from song & album articles into chapters."""
    if discography_context is None:
        discography_context = []

    formatted_discography: List[DiscographyEntry] = []
    for d in discography_context:
        if isinstance(d, DiscographyEntry):
            formatted_discography.append(d)
        elif isinstance(d, dict):
            formatted_discography.append(DiscographyEntry(
                title=d["title"],
                release_date=d.get("release_date", ""),
                allmusic_rating=d.get("allmusic_rating", "★★★★☆  4.0 / 5"),
                relationship=d.get("relationship", "Album"),
                is_current=d.get("is_current", False),
            ))

    all_articles = song_articles + album_articles
    all_text = "\n\n".join([a.full_text for a in all_articles if a.full_text])

    song_spark_paragraphs = []
    album_lore_paragraphs = []
    trivia_items = []

    # 1. Process Song-Specific Articles
    for art in song_articles:
        if not art.full_text:
            continue
        paragraphs = art.full_text.split("\n\n")
        for p in paragraphs:
            p_lower = p.lower()
            if any(w in p_lower for w in ["wrote the song", "writing session", "inspiration for", "originated", "melody came", "lyrics were about", "conceived"]):
                if len(p) > 80 and p not in song_spark_paragraphs:
                    song_spark_paragraphs.append(p)
            if any(w in p_lower for w in ["accident", "originally intended", "rejected", "almost didn't make", "trivia"]):
                if len(p) > 60 and p not in trivia_items:
                    trivia_items.append(p)

    # 2. Process Album Retrospectives
    for art in album_articles:
        if not art.full_text:
            continue
        paragraphs = art.full_text.split("\n\n")
        for p in paragraphs:
            p_lower = p.lower()
            if any(w in p_lower for w in ["in the studio", "sessions", "making of", "reunion", "direction", "sound", "recorded at", "analog", "departure"]):
                if len(p) > 80 and p not in album_lore_paragraphs:
                    album_lore_paragraphs.append(p)
            if any(w in p_lower for w in ["accident", "stairwell", "tension", "scrapped", "delay", "gap"]):
                if len(p) > 60 and p not in trivia_items:
                    trivia_items.append(p)

    # 3. Detect Studio Sanctuary & Heritage
    album_name = song.album or song.title
    fac_name, loc, why_chosen, prior_landmarks, peers = detect_studio_facility(
        song.artist, album_name, all_text
    )
    raw_prods, collabs, lead_eng = resolve_producers_and_collaborators(
        song.artist, album_name, all_text
    )
    producers = [
        ProducerPedigree(
            name=p["name"],
            role=p["role"],
            with_queried_artist=p["with_queried_artist"],
            with_related_artists=p["with_related_artists"],
        )
        for p in raw_prods
    ]
    studio_sanctuary = StudioHeritage(
        facility_name=fac_name,
        location=loc,
        why_chosen=why_chosen,
        prior_landmarks=prior_landmarks,
        contemporary_peers=peers,
        producers=producers,
        collaborators=collabs,
        lead_engineer=lead_eng,
    )

    # 4. Format Spark & Album Lore summaries
    creative_spark_summary = (
        "\n\n".join(song_spark_paragraphs[:3])
        if song_spark_paragraphs
        else (
            f"The creative spark behind {song} originated from foundational songwriting "
            f"sessions, exploring distinct textural motifs and melodic themes on '{album_name}'."
        )
    )

    album_lore_summary = (
        "\n\n".join(album_lore_paragraphs[:3])
        if album_lore_paragraphs
        else (
            f"Production accounts document the overarching recording atmosphere and creative evolution "
            f"for {song.artist}'s landmark album '{album_name}'."
        )
    )

    dossier = SongDossier(
        song=song,
        song_articles_count=len(song_articles),
        album_articles_count=len(album_articles),
        articles=all_articles,
        creative_spark=creative_spark_summary,
        album_lore=album_lore_summary,
        discography_context=formatted_discography,
        discography_summary=discography_summary,
        studio_sanctuary=studio_sanctuary,
        trivia=trivia_items[:4],
        compiled_at=datetime.now(timezone.utc),
    )

    # Save to local cache
    cache_dossier(dossier)
    return dossier
