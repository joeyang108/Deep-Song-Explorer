"""Data models for song articles, dossiers, studio heritage, and discography context."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class Song:
    """Represents a song being explored."""
    title: str
    artist: str
    year: Optional[int] = None
    album: Optional[str] = None
    original_query: Optional[str] = None
    musicbrainz_id: Optional[str] = None

    def __str__(self) -> str:
        return f'"{self.title}" by {self.artist}'


@dataclass
class Article:
    """Represents a curated article, interview, or retrospective."""
    title: str
    url: str
    source_name: str
    category: str  # e.g., 'studio_craft', 'oral_history', 'lyrics_lore', 'album_retrospective'
    snippet: str = ""
    full_text: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    key_quotes: List[str] = field(default_factory=list)
    is_album_level: bool = False


@dataclass
class DiscographyEntry:
    """Represents an album in the artist's studio timeline."""
    title: str
    release_date: str
    allmusic_rating: str
    relationship: str  # 'Preceding', '▶ CURRENT', 'Successor'
    is_current: bool = False


@dataclass
class ProducerPedigree:
    """Details landmark productions with the queried artist and other artists."""
    name: str
    role: str
    with_queried_artist: List[str] = field(default_factory=list)
    with_related_artists: List[str] = field(default_factory=list)


@dataclass
class StudioHeritage:
    """Captures the recording facility, why chosen, studio lineage, and collaborators."""
    facility_name: str
    location: str
    why_chosen: str
    prior_landmarks: List[str] = field(default_factory=list)
    contemporary_peers: List[str] = field(default_factory=list)
    producers: List[ProducerPedigree] = field(default_factory=list)
    collaborators: List[str] = field(default_factory=list)
    lead_engineer: Optional[str] = None


@dataclass
class SongDossier:
    """Comprehensive dossier synthesized from articles, lore, discography, and studio heritage."""
    song: Song
    song_articles_count: int = 0
    album_articles_count: int = 0
    articles: List[Article] = field(default_factory=list)
    creative_spark: str = ""
    album_lore: str = ""
    discography_context: List[DiscographyEntry] = field(default_factory=list)
    discography_summary: str = ""
    studio_sanctuary: Optional[StudioHeritage] = None
    trivia: List[str] = field(default_factory=list)
    compiled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
