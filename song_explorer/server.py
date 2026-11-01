"""FastAPI web server & Mobile PWA API backend for Deep Song Explorer."""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import CACHE_DIR
from .articles.models import Song, SongDossier
from .articles.search import search_dual_tier
from .articles.extractor import enrich_article
from .articles.synthesizer import (
    synthesize_dossier,
    load_cached_dossier,
    _make_cache_key,
)
from .metadata.musicbrainz import resolve_track_and_album, get_album_discography_context
from .chat import build_system_context, query_llm_response

app = FastAPI(title="Deep Song Explorer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WEB_DIR = Path(__file__).parent / "web"


class ChatRequest(BaseModel):
    artist: str
    song: str
    prompt: str
    history: List[Dict[str, str]] = []


def _load_cached_json(artist: str, song: str) -> Optional[Dict[str, Any]]:
    """Loads raw cached JSON directly for high-speed serialization."""
    key = _make_cache_key(artist, song)
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Deep Song Explorer Mobile"}


@app.get("/api/history")
def get_history():
    """Returns list of all cached dossiers for instant 1-tap mobile selection."""
    if not CACHE_DIR.exists():
        return {"items": []}

    history = []
    for f in sorted(CACHE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            s = data.get("song", {})
            history.append({
                "artist": s.get("artist", "Unknown Artist"),
                "title": s.get("title", f.stem),
                "album": s.get("album"),
                "year": s.get("year"),
                "key": f.stem,
                "facility": data.get("studio_sanctuary", {}).get("facility_name") if data.get("studio_sanctuary") else None,
                "rating": data.get("discography_context", [{}])[0].get("allmusic_rating") if data.get("discography_context") else None,
            })
        except Exception:
            continue

    return {"items": history}


@app.get("/api/dossier")
def get_dossier(
    artist: str = Query(..., description="Artist name"),
    song: str = Query(..., description="Song title"),
    refresh: bool = Query(False, description="Bypass cache and synthesize fresh"),
):
    """Fetches a Song Dossier from cache or runs dual-tier synthesis."""
    artist = artist.strip()
    song = song.strip()
    if not artist or not song:
        raise HTTPException(status_code=400, detail="Artist and song are required")

    # 1. Check cache first if not refreshing
    if not refresh:
        cached_data = _load_cached_json(artist, song)
        if cached_data:
            return {"dossier": cached_data, "source": "cache"}

    # 2. Canonical resolution via MusicBrainz
    mb_info = resolve_track_and_album(artist, song)
    canonical_song = mb_info["canonical_song"] if mb_info else song
    canonical_artist = mb_info["canonical_artist"] if mb_info else artist
    album_name = mb_info["album"] if mb_info else None
    year = mb_info["year"] if mb_info else None
    artist_id = mb_info["artist_id"] if mb_info else ""
    original_query = song if (mb_info and mb_info.get("is_corrected")) else None

    # Check cache again under canonical name
    if not refresh:
        cached_data = _load_cached_json(canonical_artist, canonical_song)
        if cached_data:
            return {"dossier": cached_data, "source": "cache"}

    # 3. Discography context
    disc_context = []
    disc_summary = ""
    if album_name and artist_id:
        disc_context, disc_summary = get_album_discography_context(
            artist_id, album_name, canonical_artist
        )

    song_obj = Song(
        title=canonical_song,
        artist=canonical_artist,
        album=album_name,
        year=year,
        original_query=original_query,
        musicbrainz_id=mb_info.get("recording_id") if mb_info else None,
    )

    # 4. Search and synthesis
    song_articles, album_articles = search_dual_tier(
        canonical_artist,
        canonical_song,
        album=album_name,
        max_song_articles=4,
        max_album_articles=4,
    )
    enriched_song_articles = [enrich_article(a) for a in song_articles]
    enriched_album_articles = [enrich_article(a) for a in album_articles]

    dossier = synthesize_dossier(
        song_obj,
        enriched_song_articles,
        enriched_album_articles,
        discography_context=disc_context,
        discography_summary=disc_summary,
    )

    # Re-load from saved cache file
    cached_data = _load_cached_json(canonical_artist, canonical_song)
    if not cached_data:
        raise HTTPException(status_code=500, detail="Failed to synthesize dossier")

    return {"dossier": cached_data, "source": "synthesized"}


@app.post("/api/chat")
def chat(req: ChatRequest):
    """Interactive AI chat endpoint grounded in the song's dossier."""
    artist = req.artist.strip()
    song = req.song.strip()
    prompt = req.prompt.strip()

    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    dossier_obj = load_cached_dossier(artist, song)
    if not dossier_obj:
        # Try resolving canonical
        mb_info = resolve_track_and_album(artist, song)
        if mb_info:
            dossier_obj = load_cached_dossier(mb_info["canonical_artist"], mb_info["canonical_song"])

    if not dossier_obj:
        raise HTTPException(status_code=404, detail="Dossier not found for this song. Please load it first.")

    system_context = build_system_context(dossier_obj)
    reply = query_llm_response(prompt, req.history, system_context)
    return {"reply": reply}


# --- PWA & Static File Routes ---

@app.get("/manifest.json")
def get_manifest():
    return FileResponse(WEB_DIR / "manifest.json", media_type="application/manifest+json")


@app.get("/sw.js")
def get_service_worker():
    return FileResponse(WEB_DIR / "sw.js", media_type="application/javascript")


@app.get("/icon.svg")
def get_icon():
    return FileResponse(WEB_DIR / "icon.svg", media_type="image/svg+xml")


if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


@app.get("/")
def get_index():
    index_file = WEB_DIR / "index.html"
    if not index_file.exists():
        return JSONResponse({"message": "Deep Song Explorer API is live. Web UI building..."})
    return FileResponse(index_file, media_type="text/html")


def run():
    """CLI launcher for local testing and server execution."""
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"\n🎵 Starting Deep Song Explorer Mobile Server on http://{host}:{port}")
    uvicorn.run("song_explorer.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    run()
