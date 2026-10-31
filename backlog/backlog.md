# Deep Song Explorer — Backlog & Parking Lot

This document captures upcoming phases, bonus ideas, and potential rabbit holes to keep active development sprints strictly bounded (45–60 minutes) and focused.

---

## 🏁 Phase Status Overview

| Phase | Milestone | Status | Notes |
| :--- | :--- | :---: | :--- |
| **Phase 1** | Making-Of Dossier & Article Finder (CLI) | **✅ LIVE** | 2-tier search, article extractor, gear scanner, Rich CLI, local caching |
| **Phase 1.5** | Local Web UI Dashboard | **⏳ Next Up** | Sleek dark-mode browser view on top of the existing Python engine |
| **Phase 2** | Lineage & Credits Engine (Discogs/MusicBrainz) | **📋 Queued** | Personnel, session players, recording studios, sample trees |
| **Phase 3** | Structural & Musical Anatomy | **📋 Queued** | BPM, key, chord progressions, arrangement breakdown |
| **Phase 4** | Stem Separation & Multi-Track Visualizer | **🔮 Future** | Local Demucs stem isolation, waveform player |

---

## 🗂️ Upcoming Work

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

### Phase 2: Lineage & Credits Engine
- [ ] **Discogs API Integration:** Fetch release credits, engineers, mixers, masterers, and session musicians.
- [ ] **MusicBrainz API Integration:** Fetch structured work relationships and recording lineage.
- [ ] **Sample & Interpolation Lineage:**
  - Track what samples were used in the song.
  - Track who later sampled or interpolated this song.
  - Explore open sample datasets or targeted scrapers.
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
- [ ] **Equipment & Gear Database Matcher:** Match gear mentioned in articles (e.g. "Roland Juno-106", "Neumann U47", "Fairchild 670") to known vintage gear specs and sound profiles.
- [ ] **"In The Studio" Photo Scraper:** Find verified studio photography from the recording sessions of historic albums.
- [ ] **Podcast & Video Essays Aggregator:** Surface episodes of *Song Exploder*, Rick Beato's *What Makes This Song Great*, or *NPR All Songs Considered* discussing the track.
