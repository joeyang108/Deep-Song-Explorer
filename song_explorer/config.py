"""Configuration and domain presets for Deep Song Explorer."""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"

# Ensure essential directories exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Curated high-signal publications for music production & deep retrospectives
CURATED_SOURCES = [
    {
        "name": "Sound On Sound",
        "domain": "soundonsound.com",
        "category": "studio_craft",
        "focus": "Microphones, mixing boards, tape machines, tracking details"
    },
    {
        "name": "Tape Op",
        "domain": "tapeop.com",
        "category": "studio_craft",
        "focus": "In-depth audio engineering interviews and creative studio approaches"
    },
    {
        "name": "Mix Online",
        "domain": "mixonline.com",
        "category": "studio_craft",
        "focus": "Classic Tracks series, recording console setup, mastering notes"
    },
    {
        "name": "Song Exploder",
        "domain": "songexploder.net",
        "category": "breakdown",
        "focus": "Artists taking apart their songs piece by piece"
    },
    {
        "name": "Pitchfork Features",
        "domain": "pitchfork.com",
        "category": "oral_history",
        "focus": "Retrospectives, making-of longforms, oral histories"
    },
    {
        "name": "Stereogum (The Number Ones)",
        "domain": "stereogum.com",
        "category": "history_lore",
        "focus": "Historical context, cultural impact, songwriting backstory"
    },
    {
        "name": "Rolling Stone Studio Stories",
        "domain": "rollingstone.com",
        "category": "history_lore",
        "focus": "Behind-the-song interviews, producer memoirs"
    },
    {
        "name": "Genius Annotations",
        "domain": "genius.com",
        "category": "lyrics_lore",
        "focus": "Verified artist annotations, lyric meanings, sample credits"
    }
]

# Targeted search intent keywords
INTENT_KEYWORDS = [
    "making of",
    "in the studio",
    "classic tracks",
    "oral history",
    "recording session",
    "behind the song",
    "how it was made",
    "isolated tracks"
]
