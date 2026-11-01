# Deep Song Explorer — Backlog & Parking Lot

This document captures upcoming phases, bonus ideas, and potential rabbit holes to keep active development sprints strictly bounded (45–60 minutes) and focused.

---

## 🏁 Phase Status Overview

| Phase | Milestone | Status | Notes |
| :--- | :--- | :---: | :--- |
| **Phase 1** | Making-Of Dossier & Article Finder (CLI) | **✅ LIVE** | 2-tier search, article extractor, Rich CLI, local caching |
| **Phase 1.2** | Album Lore, Discography Context, Studio Sanctuary & AI Chat | **🚀 ACTIVE BUILD** | Dual track+album articles, MusicBrainz resolution, 3-preceding/3-successor discography with AllMusic ratings, Studio Sanctuary (prior landmarks, peers, producer pedigree), Interactive Gen AI Chat |
| **Phase 1.5** | Local Web UI Dashboard | **⏳ Next Up** | Sleek dark-mode browser view on top of the existing Python engine |
| **Phase 2** | Lineage & Credits Engine (Spotify SongDNA / Discogs) | **📋 Queued** | Personnel, session players, WhoSampled lineage (samples/covers/interpolations) |
| **Phase 3** | Structural & Musical Anatomy | **📋 Queued** | BPM, key, chord progressions, arrangement breakdown |
| **Phase 4** | Stem Separation & Multi-Track Visualizer | **🔮 Future** | Local Demucs stem isolation, waveform player |

---

## 🗂️ Upcoming & Active Work

### Phase 1.2: Deep Cut Resolution, Studio Sanctuary, Discography Context & Gen AI Chat (Current Sprint)
- [ ] **MusicBrainz Auto-Resolution & Typo Correction:**
  - Auto-resolve typos in track names (e.g., `"Paradise Circle"` → `"Paradise Circus"`) via MusicBrainz Recording API.
  * Extract official album name, release year, artist credit, and match score.
- [ ] **Dual-Search: Song Articles & Dedicated Album Lore:**
  * Always search and display BOTH Song Articles AND Album Retrospectives.
  * Display explicit counts for both (e.g., `Found: 2 Song Articles`, `Found: 4 Album Retrospectives`).
  * Partition the deep-dive source archive table into `🎵 SONG ARTICLES` and `💽 ALBUM ARTICLES`.
- [ ] **Album Context & Discography Timeline:**
  * Position in discography (e.g. *Album 5 of 5 in Massive Attack's studio discography*).
  * Display up to **3 preceding albums** and up to **3 successor albums** in chronological order with exact release dates.
  * Fetch and display **AllMusic.com ratings** (e.g., `★★★★½ 4.5 / 5`) for each album in the timeline.
- [ ] **Studio Sanctuary & Heritage (Replacing Gear Section):**
  * **Recording Facility & Location:** Specific studio/complex (e.g. *100 Suns Studio, Bristol, UK*).
  * **Why This Studio & Artist Context:** The narrative reason why the artist recorded here in the arc of their career (e.g., fleeing London commercial studio pressure after *Mezzanine*, seeking unclocked experimentation).
  * **Notable Prior Landmark Albums:** Classic albums cut in that facility prior to this record (the studio's creative lineage).
  * **Contemporary Peers (Same Era):** Notable artists recording in that facility or immediate creative circle around the same time.
  * **Producer Pedigree & Landmark Works:**
    * Credits for producers & engineers on this record.
    * Notable landmark albums created with this artist (e.g. Neil Davidge: *Mezzanine*, *100th Window*).
    * Notable landmark albums created with other related artists (e.g. Tim Goldsworthy: *LCD Soundsystem*, *The Rapture*).
  * **Famous Collaborators & Guest Personnel:** Key guest vocalists and featured session musicians.
- [ ] **Interactive Gen AI Chat Assistant:**
  * Interactive REPL prompt at the bottom of the CLI.
  * Primed with the full dossier, album timeline, studio heritage, and scraped article text.
  * Zero-setup default via `ddgs.chat()` (free Claude 3 / GPT-4o-mini / Llama 3) with seamless fallback to `GEMINI_API_KEY` / `OPENAI_API_KEY`.
  * Allows user to ask questions (e.g., *"Why was there a 7-year gap between 100th Window and Heligoland?"*).

---

### Phase 1.5: Web UI & Rich Media Enhancements (Next Session)
- [ ] **Lightweight Local Web Dashboard:**
  - Build a dark-mode browser dashboard (FastAPI/Flask + Vanilla CSS).
  - Search bar with instant autocomplete / history of recent searches.
  - Collapsible dossier sections (Creative Spark, In the Studio, Quotes, Trivia).
  - Clickable card archive for primary source articles.
- [ ] **Embedded Audio/Video Preview:**
  - Embed YouTube or audio player so you can listen to the track or isolated solo while reading the dossier.
- [ ] **Export Feature:**
  - Single-click export of the compiled dossier to a clean Markdown or PDF document.

### Phase 2: Lineage & Credits Engine (Inspired by Spotify SongDNA)
- [ ] **Spotify SongDNA Parity:** Replicate Spotify's closed SongDNA using open data.
- [ ] **WhoSampled Integration:** Direct scraping/API for samples used, tracks sampled, and cover versions.
- [ ] **Discogs API Integration:** Fetch release credits, engineers, mixers, masterers, and session musicians.
- [ ] **Visual Lineage Graph:** Interactive tree showing musical family trees / influence chains.

### Phase 3: Structural & Musical Anatomy
- [ ] **Musical Attributes Detection:** Key detection, BPM/tempo estimation, time signature.
- [ ] **Arrangement & Section Breakdown:** Detect or parse Intro, Verse, Chorus, Bridge, Solo, Outro timestamps.
- [ ] **Chord Progression Mapping:** Visual representation of harmonic progression.
- [ ] **Lyrical Theme & Rhyme Scheme Analysis:** Analyze lyrical patterns, rhyme schemes, and recurring motifs.

### Phase 4: Audio Stem Separation & Interactive Visualizer
- [ ] **Demucs Integration:** Local offline audio stem separation into 4 stems: Vocals, Drums, Bass, Other.
- [ ] **Multi-Track Web/GUI Player:** Interactive audio player with solo/mute buttons per stem and sync playhead.
- [ ] **Frequency Spectrum & Waveform Visualizer:** Rich animated visualizer showing layers being pulled apart in real time.
- [ ] **A/B Comparison Mode:** Compare original mix vs. isolated stems seamlessly.

---

## 💡 Bonus Ideas & Explorations (Parked)
- [ ] **Spotify / Apple Music Integration:** Import a user's currently playing track or playlist directly into the explorer.
- [ ] **"In The Studio" Photo Scraper:** Find verified studio photography from the recording sessions of historic albums.
- [ ] **Podcast & Video Essays Aggregator:** Surface episodes of *Song Exploder*, Rick Beato's *What Makes This Song Great*, or *NPR All Songs Considered* discussing the track.
