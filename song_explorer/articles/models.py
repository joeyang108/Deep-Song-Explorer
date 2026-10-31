"""Data models for song articles and dossiers."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Song:
    """Represents a song being explored."""
    title: str
    artist: str
    year: Optional[int] = None
    album: Optional[str] = None

    def __str__(self) -> str:
        return f'"{self.title}" by {self.artist}'


@dataclass
class Article:
    """Represents a curated article, interview, or retrospective."""
    title: str
    url: str
    source_name: str
    category: str  # e.g., 'studio_craft', 'oral_history', 'lyrics_lore'
    snippet: str = ""
    full_text: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    key_quotes: List[str] = field(default_factory=list)
    gear_mentioned: List[str] = field(default_factory=list)


@dataclass
class SongDossier:
    """Comprehensive dossier synthesized from articles and lore."""
    song: Song
    articles: List[Article] = field(default_factory=list)
    creative_spark: str = ""
    studio_craft: str = ""
    gear_lore: List[str] = field(default_factory=list)
    trivia: List[str] = field(default_factory=list)
    compiled_at: datetime = field(default_factory=datetime.utcnow)
