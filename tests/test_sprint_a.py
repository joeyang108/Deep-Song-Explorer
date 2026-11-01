"""Automated unit and integration test suite for Phase 1.2 features."""
import pytest
from song_explorer.articles.models import Song, Article, SongDossier
from song_explorer.articles.search import generate_song_queries, generate_album_queries
from song_explorer.articles.studios import detect_studio_facility
from song_explorer.articles.producers import resolve_producers_and_collaborators
from song_explorer.metadata.musicbrainz import (
    resolve_track_and_album,
    get_album_discography_context,
    get_allmusic_rating,
)
from song_explorer.articles.synthesizer import synthesize_dossier, cache_dossier, load_cached_dossier


def test_generate_queries():
    """Validates that song and album queries generate expected intent terms."""
    song_q = generate_song_queries("Massive Attack", "Paradise Circus")
    assert any("Sound On Sound" in q for q in song_q)
    assert any("making of" in q for q in song_q)

    alb_q = generate_album_queries("Massive Attack", "Heligoland")
    assert any("Tape Op" in q for q in alb_q)
    assert any("in the studio" in q for q in alb_q)


def test_studio_sanctuary_detection():
    """Validates detection of iconic studios, prior landmarks, and peers."""
    fac, loc, why, landmarks, peers = detect_studio_facility(
        "Massive Attack", "Heligoland", "Recorded at 100 Suns in Bristol"
    )
    assert "100 Suns" in fac
    assert "Bristol" in loc
    assert len(landmarks) >= 1
    assert len(peers) >= 1
    assert "Mezzanine" in why or "bunker" in why or "isolation" in why


def test_producer_pedigree_resolution():
    """Validates producer pedigree and album collaborator resolution."""
    producers, collabs, lead_eng = resolve_producers_and_collaborators(
        "Massive Attack", "Heligoland", "Tim Goldsworthy and Neil Davidge worked on the sessions"
    )
    assert len(producers) >= 1
    names = [p["name"] for p in producers]
    assert any("Tim Goldsworthy" in n or "Neil Davidge" in n for n in names)
    
    # Check works with related artists
    tg = next((p for p in producers if "Tim Goldsworthy" in p["name"]), None)
    if tg:
        assert any("LCD Soundsystem" in w for w in tg["with_related_artists"])

    # Check collaborators
    assert any("Hope Sandoval" in c for c in collabs)
    assert lead_eng == "Euan Dickinson"


def test_musicbrainz_resolution_and_fuzzy_typo():
    """Tests MusicBrainz live resolution of track spelling variation."""
    info = resolve_track_and_album("Massive Attack", "Paradise Circle")
    if info:
        assert info["canonical_song"] == "Paradise Circus"
        assert info["album"] == "Heligoland"
        assert info["year"] == 2010
        assert info["is_corrected"] is True


def test_album_discography_timeline():
    """Tests fetching chronological studio discography and AllMusic ratings."""
    # Test AllMusic ratings mapping
    rating = get_allmusic_rating("Massive Attack", "Mezzanine")
    assert "5.0 / 5" in rating

    rating_heli = get_allmusic_rating("Massive Attack", "Heligoland")
    assert "3.5 / 5" in rating_heli


def test_synthesizer_and_cache_roundtrip(tmp_path, monkeypatch):
    """Tests synthesizing a dossier, caching to JSON, and reloading."""
    from song_explorer import config
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    from song_explorer.articles import synthesizer
    monkeypatch.setattr(synthesizer, "CACHE_DIR", tmp_path)

    song = Song(
        title="Paradise Circus",
        artist="Massive Attack",
        album="Heligoland",
        year=2010,
        original_query="Paradise Circle"
    )
    song_arts = [
        Article(
            title="Songfacts: Paradise Circus",
            url="https://songfacts.com/test",
            source_name="Songfacts",
            category="lyrics_lore",
            full_text="Grant Marshall wrote the song after reaching out to Mazzy Star's Hope Sandoval. The track was an accident."
        )
    ]
    alb_arts = [
        Article(
            title="Tape Op: Inside 100 Suns",
            url="https://tapeop.com/test",
            source_name="Tape Op",
            category="album_studio",
            is_album_level=True,
            full_text="In the studio at 100 Suns, Massive Attack reunited to record Heligoland with live instruments."
        )
    ]

    dossier = synthesize_dossier(song, song_arts, alb_arts)
    assert dossier.song_articles_count == 1
    assert dossier.album_articles_count == 1
    assert dossier.studio_sanctuary is not None
    assert "100 Suns" in dossier.studio_sanctuary.facility_name

    # Test cache roundtrip
    cached = load_cached_dossier("Massive Attack", "Paradise Circus")
    assert cached is not None
    assert cached.song.title == "Paradise Circus"
    assert cached.song.album == "Heligoland"
    assert cached.studio_sanctuary.facility_name == dossier.studio_sanctuary.facility_name
