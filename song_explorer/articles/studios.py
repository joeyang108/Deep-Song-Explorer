"""Studio Sanctuary & Heritage knowledge base and detector."""
import re
from typing import Dict, List, Optional, Tuple

# Comprehensive knowledge base of legendary recording facilities
ICONIC_STUDIOS: Dict[str, dict] = {
    "100 suns": {
        "facility_name": "100 Suns Studio",
        "location": "Bristol, UK",
        "why_chosen": (
            "Following the grueling, high-friction sessions of 'Mezzanine' at Olympic and Ridge Farm, "
            "Massive Attack constructed 100 Suns as their private, clandestine bunker in Bristol. They "
            "sought complete isolation from London industry pressure, open-ended timelines, and a private "
            "laboratory to experiment without commercial studio clock scrutiny."
        ),
        "prior_landmarks": [
            "Massive Attack — '100th Window' (2003)",
            "Massive Attack & Neil Davidge — 'Danny the Dog' OST (2004)",
        ],
        "contemporary_peers": [
            "Portishead & Adrian Utley — 'Third' era sessions (Bristol sound network)",
            "Damon Albarn / Gorillaz — 'Plastic Beach' collaborative sketches",
        ],
    },
    "sound city": {
        "facility_name": "Sound City Studios",
        "location": "Van Nuys, Los Angeles, CA",
        "why_chosen": (
            "Celebrated for its legendary, custom-built Neve 8028 console and unmatched drum room acoustics. "
            "Artists gravitated to Sound City when they wanted an uncompromisingly punchy, raw, and organic "
            "room sound captured live to tape without digital artifice."
        ),
        "prior_landmarks": [
            "Buckingham Nicks — 'Buckingham Nicks' (1973)",
            "Neil Young — 'After the Gold Rush' (1970)",
            "Fleetwood Mac — 'Fleetwood Mac' (1975)",
        ],
        "contemporary_peers": [
            "Tom Petty and the Heartbreakers — 'Damn the Torpedoes' (1979)",
            "Nirvana — 'Nevermind' (1991)",
            "Rage Against the Machine — 'Rage Against the Machine' (1992)",
        ],
    },
    "record plant sausalito": {
        "facility_name": "The Record Plant",
        "location": "Sausalito, California",
        "why_chosen": (
            "A serene waterfront residential retreat north of San Francisco. Artists fled the distractions, "
            "record-label executives, and intense personal turmoil of Los Angeles to live on-site in private "
            "bungalows and record around the clock in complete seclusion."
        ),
        "prior_landmarks": [
            "Sly and the Family Stone — 'Fresh' (1973)",
            "Stevie Wonder — 'Songs in the Key of Life' (1974–1976 sessions)",
            "Bob Dylan — 'Blood on the Tracks' (overdub sessions)",
        ],
        "contemporary_peers": [
            "Fleetwood Mac — 'Rumours' (1977)",
            "Grateful Dead — 'Terrapin Station' (1977)",
            "Rick James — 'Come Get It!' (1978)",
        ],
    },
    "village recorder": {
        "facility_name": "The Village Studios (Village Recorder)",
        "location": "Santa Monica, Los Angeles, CA",
        "why_chosen": (
            "Housed in a historic 1920s Masonic temple, The Village was famed for pristine acoustic isolation, "
            "state-of-the-art Neve boards, and a luxurious creative sanctuary where obsessive perfectionists "
            "could audition world-class session players in absolute sonic fidelity."
        ),
        "prior_landmarks": [
            "Bob Dylan — 'Planet Waves' (1974)",
            "The Rolling Stones — 'Goats Head Soup' (mixing sessions)",
        ],
        "contemporary_peers": [
            "Steely Dan — 'Aja' (1977)",
            "Fleetwood Mac — 'Tusk' (1979)",
            "Super创amp — 'Breakfast in America' (1979)",
        ],
    },
    "electric lady": {
        "facility_name": "Electric Lady Studios",
        "location": "Greenwich Village, New York City, NY",
        "why_chosen": (
            "Commissioned by Jimi Hendrix and designed by John Storyk with curved walls, ambient mood lighting, "
            "and round architectural lines. Built explicitly as an artist-centric sanctuary designed to banish "
            "the sterile, clinical feel of corporate studio spaces."
        ),
        "prior_landmarks": [
            "Jimi Hendrix — 'The Cry of Love' (1971)",
            "Stevie Wonder — 'Innervisions' & 'Talking Book' (1972–1973)",
            "Led Zeppelin — 'Houses of the Holy' (1973)",
        ],
        "contemporary_peers": [
            "David Bowie — 'Young Americans' (1975)",
            "The Clash — 'Sandinista!' (1980)",
            "D'Angelo & The Soulquarians — 'Voodoo' (2000)",
        ],
    },
    "hansa": {
        "facility_name": "Hansa Tonstudio (Hansa by the Wall)",
        "location": "Kreuzberg, West Berlin, Germany",
        "why_chosen": (
            "Perched a stone's throw from the Berlin Wall, Hansa's cavernous Meistersaal ballroom provided a grand, "
            "haunting natural reverberation and a charged Cold-War atmosphere that inspired radical artistic reinvention "
            "away from domestic comfort."
        ),
        "prior_landmarks": [
            "David Bowie — 'Low' & '\"Heroes\"' (1977)",
            "Iggy Pop — 'The Idiot' & 'Lust for Life' (1977)",
        ],
        "contemporary_peers": [
            "Depeche Mode — 'Black Celebration' (1986)",
            "U2 — 'Achtung Baby' (1991)",
            "Nick Cave and the Bad Seeds — 'The Firstborn Is Dead' (1985)",
        ],
    },
    "abbey road": {
        "facility_name": "Abbey Road Studios (Studio Two)",
        "location": "St John's Wood, London, UK",
        "why_chosen": (
            "The undisputed cathedral of British recording history. Studio Two offered massive physical room acoustics, "
            "a treasury of rare vintage microphones, and unmatched custom REDD and TG solid-state engineering pedigree."
        ),
        "prior_landmarks": [
            "The Beatles — 'Sgt. Pepper's Lonely Hearts Club Band' (1967) & 'Abbey Road' (1969)",
            "Pink Floyd — 'The Dark Side of the Moon' (1973)",
        ],
        "contemporary_peers": [
            "Radiohead — 'The Bends' & 'OK Computer' orchestral sessions (1995–1997)",
            "Oasis — 'Be Here Now' (1997)",
        ],
    },
}


def detect_studio_facility(
    artist: str,
    album: str,
    all_articles_text: str
) -> Tuple[str, str, str, List[str], List[str]]:
    """Detects the recording facility, location, why-chosen context, prior landmarks, and peers."""
    combined_text = f"{artist} {album} {all_articles_text}".lower()

    # 1. Match against known iconic studios
    for key, studio_info in ICONIC_STUDIOS.items():
        if key in combined_text or (key == "100 suns" and "massive attack" in artist.lower()):
            return (
                studio_info["facility_name"],
                studio_info["location"],
                studio_info["why_chosen"],
                studio_info["prior_landmarks"],
                studio_info["contemporary_peers"],
            )

    # 2. Dynamic regex search for studio mentions in article text
    facility_patterns = [
        r"(?:recorded|tracked|cut|mixed)\s+(?:primarily\s+)?at\s+([A-Z][A-Za-z0-9'\s]+?(?:Studios?|Sound|Plant|Recorders?|Compound|Farm|Manor|House|Room))",
        r"([A-Z][A-Za-z0-9'\s]+?(?:Studios?|Sound|Plant|Recorders?))\s+in\s+([A-Z][a-zA-Z\s,]+)",
    ]

    detected_name = None
    detected_loc = "Worldwide"
    for pat in facility_patterns:
        match = re.search(pat, all_articles_text)
        if match:
            detected_name = match.group(1).strip()
            if len(match.groups()) > 1 and match.group(2):
                detected_loc = match.group(2).strip()
            break

    if not detected_name:
        detected_name = f"{artist} Private Recording Studio"

    # Extract why-chosen context from surrounding sentences
    why_chosen = None
    context_keywords = [
        "chose", "decided to record", "retreated", "isolation", "escaped",
        "built their own", "moved to", "wanted a sound", "environment"
    ]
    for p in all_articles_text.split("\n\n"):
        p_lower = p.lower()
        if any(kw in p_lower for kw in context_keywords) and (detected_name.lower() in p_lower or "studio" in p_lower):
            why_chosen = p.strip()
            break

    if not why_chosen:
        why_chosen = (
            f"Chosen by {artist} during the sessions for '{album}' to establish an immersive, "
            f"unhurried creative environment suited to developing the record's sonic palette."
        )

    prior_landmarks = [
        f"{artist} — Career transitional recording sessions",
        f"Classic mid-era analog tracking and overdub sessions",
    ]
    contemporary_peers = [
        f"Contemporary album tracking sessions during the {album} era",
    ]

    return detected_name, detected_loc, why_chosen, prior_landmarks, contemporary_peers
