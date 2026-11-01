"""Command-line interface for Deep Song Explorer."""
import sys
import argparse
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from .articles.models import Song, SongDossier
from .articles.search import search_dual_tier
from .articles.extractor import enrich_article
from .articles.synthesizer import synthesize_dossier, load_cached_dossier
from .metadata.musicbrainz import resolve_track_and_album, get_album_discography_context
from .chat import start_chat_session

console = Console()


def display_header(song: Song, is_cached: bool = False):
    """Renders the main hero banner with album details and resolution badges."""
    cache_badge = " [bold green]⚡ [Instant Cache][/bold green]" if is_cached else ""
    album_line = f"\n[bold yellow]💽 Album:[/bold yellow]  [bold white]{song.album or 'Unknown Album'}[/bold white]"
    if song.year:
        album_line += f" [dim]({song.year})[/dim]"

    correction_badge = ""
    if song.original_query and song.original_query.strip().lower() != song.title.strip().lower():
        correction_badge = f"\n\n[bold green]✔ Auto-Resolved from:[/bold green] [dim]\"{song.original_query}\" via MusicBrainz[/dim]"

    header_content = (
        f"[bold cyan]🎵 Track:[/bold cyan]  [bold white]{song.title}[/bold white]\n"
        f"[bold magenta]👤 Artist:[/bold magenta] [bold white]{song.artist}[/bold white]{cache_badge}"
        f"{album_line}"
        f"{correction_badge}"
    )

    console.print(
        Panel(
            header_content,
            title="[bold yellow]🔍 DEEP SONG EXPLORER[/bold yellow]",
            subtitle="[dim]Making-Of Dossier & Studio Lore Engine[/dim]",
            border_style="bright_blue",
            box=box.ROUNDED,
            padding=(1, 2)
        )
    )


def display_dossier(dossier: SongDossier):
    """Renders all synthesized chapters of the dossier."""
    song = dossier.song
    album_display = song.album or "Album"
    year_str = f" ({song.year})" if song.year else ""

    # 1. Creative Spark & Song Origins
    spark_body = []
    spark_count_badge = f"[bold cyan]📊 Found: {dossier.song_articles_count} Song-Specific Articles[/bold cyan]"
    if dossier.song_articles_count == 0:
        spark_count_badge = "[bold yellow]📊 Found: 0 Song-Specific Articles — Relying on Album Lore[/bold yellow]"
    spark_body.append(spark_count_badge + "\n")
    if dossier.creative_spark:
        spark_body.append(dossier.creative_spark)

    console.print(
        Panel(
            "\n".join(spark_body),
            title="[bold green]🎙️ THE CREATIVE SPARK & SONG ORIGINS[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2)
        )
    )

    # 2. Album Context & Discography Timeline
    if dossier.discography_context:
        disc_table = Table(
            box=box.SIMPLE,
            expand=True,
            show_header=True,
            header_style="bold bright_white on blue"
        )
        disc_table.add_column("Timeline", style="cyan", width=14)
        disc_table.add_column("Released", style="dim", width=12)
        disc_table.add_column("Studio Album Title", style="white")
        disc_table.add_column("AllMusic Rating", style="bright_yellow", width=30)

        for entry in dossier.discography_context:
            if entry.is_current:
                rel_style = "[bold bright_yellow]▶ CURRENT[/bold bright_yellow]"
                title_style = f"[bold bright_white on dark_green] {entry.title} [/bold bright_white on dark_green]"
                rating_style = f"[bold bright_yellow]{entry.allmusic_rating}[/bold bright_yellow] [bold cyan]◀ CURRENT[/bold cyan]"
            else:
                rel_style = f"[dim]{entry.relationship}[/dim]"
                title_style = entry.title
                rating_style = entry.allmusic_rating

            disc_table.add_row(
                rel_style,
                entry.release_date[:10] if entry.release_date else "—",
                title_style,
                rating_style
            )

        summary_title = f"[bold cyan]📌 Position:[/bold cyan] {dossier.discography_summary}\n"
        console.print(
            Panel(
                summary_title,
                title="[bold blue]📈 ALBUM CONTEXT & DISCOGRAPHY TIMELINE[/bold blue]",
                border_style="blue",
                box=box.ROUNDED,
                padding=(1, 2)
            )
        )
        console.print(disc_table)
        console.print()

    # 3. Dedicated Album Lore & Studio Context
    album_body = []
    alb_count_badge = f"[bold magenta]📊 Found: {dossier.album_articles_count} Album Retrospectives[/bold magenta]"
    album_body.append(alb_count_badge + "\n")
    if dossier.album_lore:
        album_body.append(dossier.album_lore)

    console.print(
        Panel(
            "\n".join(album_body),
            title=f"[bold magenta]💽 ALBUM LORE & CONTEXT: {album_display.upper()}{year_str}[/bold magenta]",
            border_style="magenta",
            box=box.ROUNDED,
            padding=(1, 2)
        )
    )

    # 4. Studio Sanctuary & Heritage (Facility, Why Chosen, Prior Landmarks, Peers, Producers, Collaborators)
    if dossier.studio_sanctuary:
        s = dossier.studio_sanctuary
        studio_sections = []

        # Facility & Location
        studio_sections.append(f"[bold yellow]📍 Recording Facility:[/bold yellow]  [bold white]{s.facility_name} ({s.location})[/bold white]\n")

        # Why Chosen & Artist Context
        studio_sections.append(f"[bold cyan]📜 Why This Studio & Artist Context:[/bold cyan]\n{s.why_chosen}\n")

        # Prior Landmark Albums
        if s.prior_landmarks:
            landmarks_text = "\n".join([f"• {lm}" for lm in s.prior_landmarks])
            studio_sections.append(f"[bold magenta]🕰️ Notable Prior Landmark Albums at this Facility:[/bold magenta]\n{landmarks_text}\n")

        # Contemporary Peers
        if s.contemporary_peers:
            peers_text = "\n".join([f"• {cp}" for cp in s.contemporary_peers])
            studio_sections.append(f"[bold bright_blue]⚡ Contemporary Peers & Era Sessions:[/bold bright_blue]\n{peers_text}\n")

        # Producer Pedigree
        if s.producers:
            prod_lines = []
            for p in s.producers:
                prod_lines.append(f"[bold white]• {p.name}[/bold white] [dim]({p.role})[/dim]:")
                if p.with_queried_artist:
                    prod_lines.append(f"  [cyan]- With this Artist:[/cyan] {', '.join(p.with_queried_artist)}")
                if p.with_related_artists:
                    prod_lines.append(f"  [magenta]- With Related Artists:[/magenta] {', '.join(p.with_related_artists)}")
            studio_sections.append(f"[bold green]🎚️ Producer Pedigree & Landmark Works:[/bold green]\n" + "\n".join(prod_lines) + "\n")

        # Famous Collaborators & Personnel
        if s.collaborators:
            collab_lines = []
            collab_lines.append(f"[bold white]• Guest Vocalists & Musicians:[/bold white] " + ", ".join(s.collaborators))
            if s.lead_engineer:
                collab_lines.append(f"[bold white]• Lead Tracking Engineer:[/bold white] {s.lead_engineer}")
            studio_sections.append(f"[bold bright_yellow]🤝 Famous Collaborators & Personnel on this Album:[/bold bright_yellow]\n" + "\n".join(collab_lines))

        console.print(
            Panel(
                "\n".join(studio_sections),
                title="[bold yellow]🏛️ STUDIO SANCTUARY & HERITAGE[/bold yellow]",
                border_style="yellow",
                box=box.ROUNDED,
                padding=(1, 2)
            )
        )

    # 5. Key Quotes & Anecdotes
    all_quotes = []
    for a in dossier.articles:
        for q in a.key_quotes:
            scope_tag = "[Album Feature]" if a.is_album_level else "[Song Feature]"
            all_quotes.append((q, a.source_name, scope_tag))

    if all_quotes:
        quote_texts = []
        for q, src, scope in all_quotes[:4]:
            quote_texts.append(f'💬 "[italic]{q}[/italic]"\n   [dim]— Source: {src} {scope}[/dim]')
        
        console.print(
            Panel(
                "\n\n".join(quote_texts),
                title="[bold magenta]💬 KEY QUOTES & ANECDOTES[/bold magenta]",
                border_style="magenta",
                box=box.ROUNDED,
                padding=(1, 2)
            )
        )

    # 6. Quirks & Trivia
    if dossier.trivia:
        trivia_lines = "\n".join([f"• {t}" for t in dossier.trivia])
        console.print(
            Panel(
                trivia_lines,
                title="[bold cyan]💡 TRIVIA & HAPPY ACCIDENTS[/bold cyan]",
                border_style="cyan",
                box=box.ROUNDED,
                padding=(1, 2)
            )
        )

    # 7. Deep-Dive Source Archive Partitioned
    table = Table(
        title="📚 DEEP-DIVE ARTICLE ARCHIVE",
        box=box.SIMPLE_HEAVY,
        header_style="bold bright_white on blue",
        expand=True
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Publication", style="bold cyan", width=22)
    table.add_column("Article Title & Direct Link", style="white")
    table.add_column("Scope & Category", style="magenta", width=24)

    song_arts = [a for a in dossier.articles if not a.is_album_level]
    alb_arts = [a for a in dossier.articles if a.is_album_level]

    idx = 1
    if song_arts:
        table.add_section()
        for art in song_arts:
            link_text = f"[link={art.url}]{art.title}[/link]\n[dim blue]{art.url}[/dim blue]"
            table.add_row(
                str(idx),
                art.source_name,
                link_text,
                f"🎵 Song • {art.category.replace('_', ' ').title()}"
            )
            idx += 1

    if alb_arts:
        table.add_section()
        for art in alb_arts:
            link_text = f"[link={art.url}]{art.title}[/link]\n[dim blue]{art.url}[/dim blue]"
            table.add_row(
                str(idx),
                art.source_name,
                link_text,
                f"💽 Album • {art.category.replace('_', ' ').title()}"
            )
            idx += 1

    console.print(table)
    console.print(f"\n[dim green]✔ Dossier compiled. Saved to local cache.[/dim green]\n")


def explore_song(artist: str, song: str, use_cache: bool = True, launch_chat: bool = True):
    """Main orchestration flow."""
    # 1. Check MusicBrainz for canonical track title, album, and discography
    with console.status("[bold cyan]🔍 Step 1/3: Resolving track & album via MusicBrainz...[/bold cyan]") as status:
        mb_info = resolve_track_and_album(artist, song)
        
        canonical_song = mb_info["canonical_song"] if mb_info else song
        canonical_artist = mb_info["canonical_artist"] if mb_info else artist
        album_name = mb_info["album"] if mb_info else None
        year = mb_info["year"] if mb_info else None
        artist_id = mb_info["artist_id"] if mb_info else ""
        original_query = song if (mb_info and mb_info.get("is_corrected")) else None

        song_obj = Song(
            title=canonical_song,
            artist=canonical_artist,
            album=album_name,
            year=year,
            original_query=original_query,
            musicbrainz_id=mb_info.get("recording_id") if mb_info else None,
        )

        disc_context = []
        disc_summary = ""
        if album_name and artist_id:
            disc_context, disc_summary = get_album_discography_context(
                artist_id, album_name, canonical_artist
            )

    # 2. Check local disk cache
    if use_cache:
        cached = load_cached_dossier(canonical_artist, canonical_song)
        if cached:
            display_header(cached.song, is_cached=True)
            display_dossier(cached)
            if launch_chat:
                start_chat_session(cached, console)
            return

    display_header(song_obj, is_cached=False)

    # 3. Dual-Tier Search & Article Enrichment
    with console.status("[bold cyan]📖 Step 2/3: Scanning song & album archives...[/bold cyan]") as status:
        song_articles, album_articles = search_dual_tier(
            canonical_artist,
            canonical_song,
            album=album_name,
            max_song_articles=4,
            max_album_articles=4
        )

        status.update(
            f"[bold cyan]📖 Reading {len(song_articles)} song articles & {len(album_articles)} album retrospectives...[/bold cyan]"
        )

        enriched_song_articles = [enrich_article(a) for a in song_articles]
        enriched_album_articles = [enrich_article(a) for a in album_articles]

        status.update("[bold cyan]🧠 Step 3/3: Synthesizing Studio Sanctuary, Discography Timeline & Lore...[/bold cyan]")
        dossier = synthesize_dossier(
            song_obj,
            enriched_song_articles,
            enriched_album_articles,
            discography_context=disc_context,
            discography_summary=disc_summary,
        )

    display_dossier(dossier)

    if launch_chat:
        start_chat_session(dossier, console)


def main():
    parser = argparse.ArgumentParser(description="Deep Song Explorer — Making-Of, Studio Sanctuary & Lore Engine")
    parser.add_argument("artist", nargs="?", help="Artist name (e.g., 'Massive Attack' or 'Steely Dan')")
    parser.add_argument("song", nargs="?", help="Song title (e.g., 'Paradise Circus' or 'Deacon Blues')")
    parser.add_argument("--no-cache", action="store_true", help="Bypass local cache and perform fresh search")
    parser.add_argument("--no-chat", action="store_true", help="Skip the interactive Gen AI chat assistant")

    args = parser.parse_args()

    artist = args.artist
    song = args.song

    # Interactive mode if arguments are missing
    if not artist or not song:
        console.print("[bold yellow]👋 Welcome to Deep Song Explorer![/bold yellow]")
        try:
            artist = console.input("[bold magenta]👤 Enter Artist Name: [/bold magenta]").strip()
            song = console.input("[bold cyan]🎵 Enter Song Title:  [/bold cyan]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Aborted.[/dim]")
            sys.exit(0)

    if not artist or not song:
        console.print("[bold red]Artist and Song are required.[/bold red]")
        sys.exit(1)

    explore_song(
        artist,
        song,
        use_cache=not args.no_cache,
        launch_chat=not args.no_chat
    )


if __name__ == "__main__":
    main()
