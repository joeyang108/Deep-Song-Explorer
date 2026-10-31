"""Command-line interface for Deep Song Explorer."""
import sys
import argparse
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from .articles.models import Song, SongDossier
from .articles.search import search_articles
from .articles.extractor import enrich_article
from .articles.synthesizer import synthesize_dossier, load_cached_dossier

console = Console()


def display_header(artist: str, song: str, is_cached: bool = False):
    """Renders the main hero banner."""
    cache_badge = " [bold green]⚡ [Instant Cache][/bold green]" if is_cached else ""
    header_content = (
        f"[bold cyan]🎵 Track:[/bold cyan] [bold white]{song}[/bold white]\n"
        f"[bold magenta]👤 Artist:[/bold magenta] [bold white]{artist}[/bold white]{cache_badge}"
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
    """Renders the synthesized dossier and source archive."""
    # 1. Creative Spark
    if dossier.creative_spark:
        console.print(
            Panel(
                dossier.creative_spark,
                title="[bold green]🎙️ THE CREATIVE SPARK & ORIGINS[/bold green]",
                border_style="green",
                box=box.ROUNDED,
                padding=(1, 2)
            )
        )

    # 2. Studio Craft & Gear Lore
    studio_body = []
    if dossier.studio_craft:
        studio_body.append(dossier.studio_craft)

    if dossier.gear_lore:
        gear_badges = "  ".join([f"[black on bright_yellow] {g} [/black on bright_yellow]" for g in dossier.gear_lore])
        studio_body.append(f"\n[bold yellow]🎛️ Gear & Instruments Detected:[/bold yellow]\n{gear_badges}")

    if studio_body:
        console.print(
            Panel(
                "\n\n".join(studio_body),
                title="[bold yellow]🎛️ IN THE STUDIO & GEAR LORE[/bold yellow]",
                border_style="yellow",
                box=box.ROUNDED,
                padding=(1, 2)
            )
        )

    # 3. Key Quotes
    all_quotes = []
    for a in dossier.articles:
        for q in a.key_quotes:
            all_quotes.append((q, a.source_name))

    if all_quotes:
        quote_texts = []
        for q, src in all_quotes[:4]:
            quote_texts.append(f'💬 "[italic]{q}[/italic]"\n   [dim]— Source: {src}[/dim]')
        
        console.print(
            Panel(
                "\n\n".join(quote_texts),
                title="[bold magenta]💬 KEY QUOTES & ANECDOTES[/bold magenta]",
                border_style="magenta",
                box=box.ROUNDED,
                padding=(1, 2)
            )
        )

    # 4. Quirks & Trivia
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

    # 5. Deep-Dive Source Archive
    table = Table(
        title="📚 DEEP-DIVE ARTICLE ARCHIVE",
        box=box.SIMPLE_HEAVY,
        header_style="bold bright_white on blue",
        expand=True
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Publication", style="bold cyan", width=22)
    table.add_column("Article Title & Direct Link", style="white")
    table.add_column("Category", style="magenta", width=16)

    for idx, art in enumerate(dossier.articles, 1):
        link_text = f"[link={art.url}]{art.title}[/link]\n[dim blue]{art.url}[/dim blue]"
        table.add_row(
            str(idx),
            art.source_name,
            link_text,
            art.category.replace("_", " ").title()
        )

    console.print(table)
    console.print(f"\n[dim green]✔ Dossier compiled at {dossier.compiled_at.strftime('%Y-%m-%d %H:%M:%S UTC')}. Saved to local cache.[/dim green]\n")


def explore_song(artist: str, song: str, use_cache: bool = True):
    """Main orchestration flow."""
    # Check cache first
    if use_cache:
        cached = load_cached_dossier(artist, song)
        if cached:
            display_header(artist, song, is_cached=True)
            display_dossier(cached)
            return

    display_header(artist, song, is_cached=False)

    with console.status("[bold cyan]🔍 Step 1/3: Scanning high-signal music archives...[/bold cyan]") as status:
        articles = search_articles(artist, song, max_total=6)
        
        if not articles:
            console.print("[bold red]❌ No high-signal articles found. Try broadening the artist or song title.[/bold red]")
            return

        status.update(f"[bold cyan]📖 Step 2/3: Reading {len(articles)} articles and parsing studio accounts...[/bold cyan]")
        enriched_articles = []
        for art in articles:
            enriched = enrich_article(art)
            enriched_articles.append(enriched)

        status.update("[bold cyan]🧠 Step 3/3: Synthesizing Song Dossier & Gear Lore...[/bold cyan]")
        song_obj = Song(title=song, artist=artist)
        dossier = synthesize_dossier(song_obj, enriched_articles)

    display_dossier(dossier)


def main():
    parser = argparse.ArgumentParser(description="Deep Song Explorer — Making-Of & Studio Lore Engine")
    parser.add_argument("artist", nargs="?", help="Artist name (e.g., 'Steely Dan')")
    parser.add_argument("song", nargs="?", help="Song title (e.g., 'Deacon Blues')")
    parser.add_argument("--no-cache", action="store_true", help="Bypass local cache and perform fresh search")

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

    explore_song(artist, song, use_cache=not args.no_cache)


if __name__ == "__main__":
    main()
