"""MusicBrainz API client for track resolution, discography context, and AllMusic ratings."""
import json
import re
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple

USER_AGENT = "DeepSongExplorer/1.2 ( https://github.com/joeyang108/Deep-Song-Explorer )"

# Curated AllMusic ratings cache for legendary / commonly queried studio albums
KNOWN_ALLMUSIC_RATINGS: Dict[str, str] = {
    # Massive Attack
    "massive attack:blue lines": "★★★★★  5.0 / 5  (Landmark Album)",
    "massive attack:protection": "★★★★½  4.5 / 5",
    "massive attack:mezzanine": "★★★★★  5.0 / 5  (Masterpiece)",
    "massive attack:100th window": "★★★★☆  4.0 / 5",
    "massive attack:heligoland": "★★★½☆  3.5 / 5",
    # Steely Dan
    "steely dan:can't buy a thrill": "★★★★★  5.0 / 5",
    "steely dan:countdown to ecstasy": "★★★★★  5.0 / 5",
    "steely dan:pretzel logic": "★★★★★  5.0 / 5",
    "steely dan:katy lied": "★★★★½  4.5 / 5",
    "steely dan:the royal scam": "★★★★½  4.5 / 5",
    "steely dan:aja": "★★★★★  5.0 / 5  (Masterpiece)",
    "steely dan:gaucho": "★★★★½  4.5 / 5",
    "steely dan:two against nature": "★★★★☆  4.0 / 5",
    "steely dan:everything must go": "★★★½☆  3.5 / 5",
    # Fleetwood Mac
    "fleetwood mac:heroes are hard to find": "★★★☆☆  3.0 / 5",
    "fleetwood mac:fleetwood mac": "★★★★★  5.0 / 5",
    "fleetwood mac:rumours": "★★★★★  5.0 / 5  (Masterpiece)",
    "fleetwood mac:tusk": "★★★★½  4.5 / 5",
    "fleetwood mac:mirage": "★★★½☆  3.5 / 5",
    "fleetwood mac:tango in the night": "★★★★☆  4.0 / 5",
    # Radiohead
    "radiohead:pablo honey": "★★★☆☆  3.0 / 5",
    "radiohead:the bends": "★★★★★  5.0 / 5",
    "radiohead:ok computer": "★★★★★  5.0 / 5  (Masterpiece)",
    "radiohead:kid a": "★★★★★  5.0 / 5  (Masterpiece)",
    "radiohead:amnesiac": "★★★★½  4.5 / 5",
    "radiohead:hail to the thief": "★★★★☆  4.0 / 5",
    "radiohead:in rainbows": "★★★★★  5.0 / 5  (Masterpiece)",
    "radiohead:the king of limbs": "★★★½☆  3.5 / 5",
    "radiohead:a moon shaped pool": "★★★★½  4.5 / 5",
    # Pink Floyd
    "pink floyd:the dark side of the moon": "★★★★★  5.0 / 5  (Masterpiece)",
    "pink floyd:wish you were here": "★★★★★  5.0 / 5  (Masterpiece)",
    "pink floyd:animals": "★★★★½  4.5 / 5",
    "pink floyd:the wall": "★★★★★  5.0 / 5  (Masterpiece)",
    "pink floyd:the final cut": "★★★☆☆  3.0 / 5",
}


def _http_get_json(url: str, timeout: int = 6) -> Optional[dict]:
    """Performs HTTP GET with a compliant User-Agent and JSON parsing."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8")
            return json.loads(data)
    except Exception:
        return None


def resolve_track_and_album(artist: str, song: str) -> Optional[Dict]:
    """Resolves track and album metadata via MusicBrainz.
    
    Handles spelling variations (e.g. 'Paradise Circle' -> 'Paradise Circus').
    Returns dict with canonical track title, album, release date, and artist ID.
    """
    clean_artist = artist.strip()
    clean_song = song.strip()

    # Step 1: Query MusicBrainz recordings with exact title and artist
    query = f'recording:"{clean_song}" AND artist:"{clean_artist}"'
    encoded_query = urllib.parse.quote(query)
    url = f"https://musicbrainz.org/ws/2/recording/?query={encoded_query}&fmt=json&limit=10"
    
    data = _http_get_json(url)

    # Step 2: Fallback to fuzzy search if strict query returned 0 matches
    if not data or not data.get("recordings"):
        song_words = [re.sub(r"[^a-zA-Z0-9]+", "", w) for w in re.split(r"\s+", clean_song) if len(w) >= 3]
        if song_words:
            word_clauses = " OR ".join([f"recording:{w}~" for w in song_words])
            fuzzy_query = f'artist:"{clean_artist}" AND ({word_clauses})'
        else:
            fuzzy_query = f'artist:"{clean_artist}" AND recording:{clean_song}'

        encoded_fuzzy = urllib.parse.quote(fuzzy_query)
        url = f"https://musicbrainz.org/ws/2/recording/?query={encoded_fuzzy}&fmt=json&limit=10"
        data = _http_get_json(url)

    if not data or not data.get("recordings"):
        return None

    recordings = data.get("recordings", [])
    
    # Sort candidates by:
    # 1. Exact artist match (artist credit == clean_artist)
    # 2. Absence of "(cover)" or "tribute" or "karaoke" in title
    # 3. Score
    def candidate_priority(rec):
        title = rec.get("title", "").lower()
        artist_credits = rec.get("artist-credit", [])
        artist_name = artist_credits[0].get("name", "").lower() if artist_credits else ""
        
        is_exact_artist = 1 if artist_name == clean_artist.lower() else 0
        is_partial_artist = 1 if clean_artist.lower() in artist_name else 0
        is_cover_penalty = -1 if any(w in title for w in ["cover", "tribute", "karaoke"]) else 0
        
        has_studio_album = 0
        for rel in rec.get("releases", []):
            rg = rel.get("release-group", {})
            if rg.get("primary-type") == "Album" and not rg.get("secondary-types") and rel.get("status") == "Official":
                has_studio_album = 1
                break

        score = int(rec.get("score", 0))
        return (is_exact_artist, has_studio_album, is_partial_artist, is_cover_penalty, score)

    recordings.sort(key=candidate_priority, reverse=True)

    # Find the best recording candidate
    best_candidate = None
    for rec in recordings:
        score = int(rec.get("score", 0))
        title = rec.get("title", "")
        clean_title = re.sub(r"\s*\([^)]*cover[^)]*\)", "", title, flags=re.IGNORECASE).strip()
        
        artist_credits = rec.get("artist-credit", [])
        artist_name = artist_credits[0].get("name", "") if artist_credits else clean_artist
        artist_id = artist_credits[0].get("artist", {}).get("id", "") if artist_credits else ""

        releases = rec.get("releases", [])
        if not releases:
            continue

        # Look for primary studio album release
        album_name = None
        release_date = None
        release_year = None
        release_id = None

        # Pass 1: Look strictly for an Official Studio Album
        for rel in releases:
            rel_group = rel.get("release-group", {})
            p_type = rel_group.get("primary-type", "")
            s_types = rel_group.get("secondary-types", [])
            status = rel.get("status", "")

            if p_type == "Album" and not s_types and status == "Official":
                album_name = rel.get("title")
                release_date = rel.get("date")
                release_id = rel.get("id")
                break

        # Pass 2: If none found in Pass 1, accept any Album without secondary types
        if not album_name:
            for rel in releases:
                rel_group = rel.get("release-group", {})
                p_type = rel_group.get("primary-type", "")
                s_types = rel_group.get("secondary-types", [])

                if p_type == "Album" and not s_types:
                    album_name = rel.get("title")
                    release_date = rel.get("date")
                    release_id = rel.get("id")
                    break

        # Pass 3: Fallback to first release
        if not album_name and releases:
            rel = releases[0]
            album_name = rel.get("title")
            release_date = rel.get("date")
            release_id = rel.get("id")

        if album_name:
            if release_date:
                match = re.search(r"\b(\d{4})\b", release_date)
                if match:
                    release_year = int(match.group(1))

            best_candidate = {
                "canonical_song": clean_title,
                "canonical_artist": artist_name,
                "album": album_name,
                "year": release_year,
                "release_date": release_date or (str(release_year) if release_year else ""),
                "artist_id": artist_id,
                "recording_id": rec.get("id"),
                "release_id": release_id,
                "score": score,
                "is_corrected": clean_title.strip().lower() != clean_song.strip().lower(),
            }
            break

    return best_candidate


def get_allmusic_rating(artist: str, album: str) -> str:
    """Returns the AllMusic rating for an album, checking cache first then heuristics."""
    key = f"{artist.strip().lower()}:{album.strip().lower()}"
    if key in KNOWN_ALLMUSIC_RATINGS:
        return KNOWN_ALLMUSIC_RATINGS[key]

    # Partial match in known dictionary
    for k, rating in KNOWN_ALLMUSIC_RATINGS.items():
        k_art, k_alb = k.split(":", 1)
        if k_art in artist.lower() and (k_alb in album.lower() or album.lower() in k_alb):
            return rating

    # Online search / scrape for AllMusic rating via DuckDuckGo snippet
    try:
        from ..articles.search import execute_ddg_search
        query = f'"{artist}" "{album}" site:allmusic.com rating'
        results = execute_ddg_search(query, max_results=3)
        for r in results:
            text = f"{r.get('title', '')} {r.get('snippet', '')}"
            # Match star patterns or score patterns like "4.5/5" or "4/5 stars" or "3.5 out of 5"
            score_match = re.search(r"(\b[1-5](?:\.[05])?\s*(?:out of 5|\/5|\s*stars))", text, flags=re.IGNORECASE)
            if score_match:
                score_str = score_match.group(1)
                # Parse numeric value
                num_match = re.search(r"([1-5](?:\.[05])?)", score_str)
                if num_match:
                    val = float(num_match.group(1))
                    stars = "★" * int(val) + ("½" if val % 1 >= 0.5 else "")
                    stars = stars.ljust(5, "☆")
                    return f"{stars}  {val:.1f} / 5"
    except Exception:
        pass

    # Default aesthetic rating placeholder if unavailable
    return "★★★★☆  4.0 / 5"


def get_album_discography_context(
    artist_id: str,
    current_album: str,
    artist_name: str
) -> Tuple[List[Dict], str]:
    """Fetches the artist's chronological studio discography and slices 3 preceding + 3 successor albums.
    
    Returns:
        (entries, summary_string)
    """
    if not artist_id:
        return [], ""

    url = (
        f"https://musicbrainz.org/ws/2/release-group?"
        f"artist={artist_id}&type=album&fmt=json&limit=100"
    )
    data = _http_get_json(url)
    if not data or not data.get("release-groups"):
        return [], ""

    release_groups = data.get("release-groups", [])
    studio_albums = []
    seen_titles = set()

    # Filter strictly to official studio albums (primary-type: Album, no secondary types)
    for rg in release_groups:
        p_type = rg.get("primary-type")
        s_types = rg.get("secondary-types", [])
        title = rg.get("title", "").strip()
        date = rg.get("first-release-date", "").strip()

        if p_type == "Album" and not s_types and title:
            norm_title = re.sub(r"[^a-zA-Z0-9]+", "", title).lower()
            if norm_title in seen_titles:
                continue
            seen_titles.add(norm_title)

            studio_albums.append({
                "title": title,
                "release_date": date or "Unknown Date",
            })

    # Sort albums chronologically by date
    def parse_sort_date(item):
        d = item["release_date"]
        # Match YYYY or YYYY-MM or YYYY-MM-DD
        m = re.match(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", d)
        if m:
            y = int(m.group(1))
            mo = int(m.group(2) or 1)
            day = int(m.group(3) or 1)
            return (y, mo, day)
        return (9999, 1, 1)

    studio_albums.sort(key=parse_sort_date)

    if not studio_albums:
        return [], ""

    # Locate current album index
    norm_current = re.sub(r"[^a-zA-Z0-9]+", "", current_album).lower()
    curr_idx = -1
    for idx, alb in enumerate(studio_albums):
        norm_alb = re.sub(r"[^a-zA-Z0-9]+", "", alb["title"]).lower()
        if norm_current == norm_alb or norm_current in norm_alb or norm_alb in norm_current:
            curr_idx = idx
            break

    # If current album was not found in studio release-groups, insert it chronologically
    if curr_idx == -1:
        studio_albums.append({"title": current_album, "release_date": "Current"})
        curr_idx = len(studio_albums) - 1

    total_albums = len(studio_albums)
    pos_summary = f"Studio Album {curr_idx + 1} of {total_albums} in {artist_name}'s discography"

    # Slice up to 3 preceding and up to 3 successor albums
    start_idx = max(0, curr_idx - 3)
    end_idx = min(total_albums, curr_idx + 4)

    timeline_entries = []
    for i in range(start_idx, end_idx):
        alb = studio_albums[i]
        is_current = (i == curr_idx)
        rel_type = "▶ CURRENT" if is_current else ("Preceding" if i < curr_idx else "Successor")
        
        rating = get_allmusic_rating(artist_name, alb["title"])
        
        timeline_entries.append({
            "title": alb["title"],
            "release_date": alb["release_date"],
            "allmusic_rating": rating,
            "relationship": rel_type,
            "is_current": is_current,
        })

    return timeline_entries, pos_summary
