"""Metadata resolution and external music database integrations."""
from .musicbrainz import resolve_track_and_album, get_album_discography_context

__all__ = ["resolve_track_and_album", "get_album_discography_context"]
