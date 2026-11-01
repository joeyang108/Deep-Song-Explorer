/**
 * Deep Song Explorer — Mobile PWA Client Application Logic
 */

let currentDossier = null;
let chatHistory = [];

document.addEventListener('DOMContentLoaded', () => {
  // 1. Register Service Worker for PWA
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch((err) => {
        console.warn('SW registration failed:', err);
      });
    });
  }

  // 2. Initialize UI Event Handlers
  initTabNavigation();
  initSearchDrawer();
  initChatSystem();
  loadHistoryChips();
});

/* =====================================================================
   TAB NAVIGATION SYSTEM
   ===================================================================== */
function initTabNavigation() {
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabPanels = document.querySelectorAll('.tab-panel');

  tabButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');

      tabButtons.forEach((b) => b.classList.remove('active'));
      tabPanels.forEach((p) => p.classList.remove('active'));

      btn.classList.add('active');
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) {
        targetPanel.classList.add('active');
      }

      // Scroll to top of panel smoothly
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  });
}

/* =====================================================================
   SEARCH & HISTORY DRAWER
   ===================================================================== */
function initSearchDrawer() {
  const toggleBtn = document.getElementById('search-toggle-btn');
  const drawer = document.getElementById('search-drawer');
  const searchForm = document.getElementById('search-form');
  const refreshBtn = document.getElementById('refresh-dossier-btn');

  toggleBtn.addEventListener('click', () => {
    drawer.classList.toggle('collapsed');
  });

  refreshBtn.addEventListener('click', () => {
    if (!currentDossier || !currentDossier.song) {
      alert('Please select or search a song first.');
      return;
    }
    fetchDossier(currentDossier.song.artist, currentDossier.song.title, true);
  });

  searchForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const artist = document.getElementById('artist-input').value.trim();
    const song = document.getElementById('song-input').value.trim();

    if (!artist || !song) return;

    fetchDossier(artist, song, false);
    drawer.classList.add('collapsed');
  });
}

/* =====================================================================
   LOAD HISTORY CHIPS
   ===================================================================== */
async function loadHistoryChips() {
  const container = document.getElementById('history-chips-container');
  const countBadge = document.getElementById('history-count');

  try {
    const res = await fetch('/api/history');
    const data = await res.json();
    const items = data.items || [];

    countBadge.textContent = items.length;
    container.innerHTML = '';

    if (items.length === 0) {
      container.innerHTML = '<span class="chip-skeleton">No cached songs yet. Search above!</span>';
      return;
    }

    items.forEach((item) => {
      const chip = document.createElement('button');
      chip.className = 'chip-btn';
      chip.type = 'button';
      chip.innerHTML = `
        <span class="chip-artist">${escapeHtml(item.artist)}</span>
        <span>${escapeHtml(item.title)}</span>
      `;
      chip.addEventListener('click', () => {
        fetchDossier(item.artist, item.title, false);
        document.getElementById('search-drawer').classList.add('collapsed');
      });
      container.appendChild(chip);
    });

    // Auto-load the first/most recent item if no song is loaded yet
    if (!currentDossier && items.length > 0) {
      fetchDossier(items[0].artist, items[0].title, false);
    }
  } catch (err) {
    console.error('Error loading history:', err);
    container.innerHTML = '<span class="chip-skeleton">Failed to load cached items</span>';
  }
}

/* =====================================================================
   FETCH & RENDER DOSSIER
   ===================================================================== */
async function fetchDossier(artist, song, refresh = false) {
  showLoading(true, `Digging into "${song}" by ${artist}...`);

  try {
    const url = `/api/dossier?artist=${encodeURIComponent(artist)}&song=${encodeURIComponent(song)}&refresh=${refresh}`;
    const res = await fetch(url);

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Server error (${res.status})`);
    }

    const json = await res.json();
    currentDossier = json.dossier;
    renderDossier(json.dossier, json.source);
  } catch (err) {
    alert(`Could not load dossier: ${err.message}`);
  } finally {
    showLoading(false);
  }
}

function renderDossier(dossier, source = 'cache') {
  if (!dossier || !dossier.song) return;

  const song = dossier.song;

  // 1. Hero Card
  document.getElementById('hero-song-title').textContent = song.title;
  document.getElementById('hero-artist-name').textContent = song.artist;
  document.getElementById('hero-album-name').textContent = song.album || 'Unknown Album';
  document.getElementById('hero-release-year').textContent = song.year || '—';

  const sourceBadge = document.getElementById('badge-source');
  sourceBadge.textContent = source === 'cache' ? '⚡ Instant Cache' : '🌐 Fresh Scraped';

  const resolvedBadge = document.getElementById('badge-resolved');
  if (song.original_query && song.original_query.toLowerCase() !== song.title.toLowerCase()) {
    resolvedBadge.classList.remove('hidden');
    resolvedBadge.textContent = `Auto-Resolved from "${song.original_query}"`;
  } else {
    resolvedBadge.classList.add('hidden');
  }

  // 2. Tab 1: Spark & Lore
  const sparkEl = document.getElementById('spark-body-content');
  if (dossier.creative_spark) {
    sparkEl.innerHTML = dossier.creative_spark
      .split('\n\n')
      .map((p) => `<p>${escapeHtml(p)}</p>`)
      .join('');
  } else {
    sparkEl.innerHTML = '<p>No creative spark accounts found for this track.</p>';
  }

  // Trivia
  const triviaContainer = document.getElementById('trivia-container');
  triviaContainer.innerHTML = '';
  if (dossier.trivia && dossier.trivia.length > 0) {
    dossier.trivia.forEach((t) => {
      const div = document.createElement('div');
      div.className = 'trivia-item';
      div.textContent = t;
      triviaContainer.appendChild(div);
    });
  } else {
    triviaContainer.innerHTML = '<div class="trivia-item">No specific happy accidents or trivia archived.</div>';
  }

  // Articles Archive
  const articlesContainer = document.getElementById('articles-container');
  articlesContainer.innerHTML = '';
  if (dossier.articles && dossier.articles.length > 0) {
    dossier.articles.forEach((a) => {
      const link = document.createElement('a');
      link.className = 'article-row-link';
      link.href = a.url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.innerHTML = `
        <span class="art-title">${escapeHtml(a.title)}</span>
        <span class="art-pub">${escapeHtml(a.source_name || 'Link ↗')}</span>
      `;
      articlesContainer.appendChild(link);
    });
  } else {
    articlesContainer.innerHTML = '<p class="timeline-hint">No external article links archived.</p>';
  }

  // 3. Tab 2: Studio Sanctuary
  const sanctuary = dossier.studio_sanctuary;
  if (sanctuary) {
    document.getElementById('facility-name-text').textContent = sanctuary.facility_name || 'Sanctuary Facility';
    document.getElementById('facility-location-text').textContent = sanctuary.location || 'Undisclosed Location';
    document.getElementById('why-chosen-text').textContent = sanctuary.why_chosen || 'Chosen for private artistic isolation.';

    // Prior landmarks
    const landmarksList = document.getElementById('prior-landmarks-list');
    landmarksList.innerHTML = '';
    (sanctuary.prior_landmarks || []).forEach((lm) => {
      const li = document.createElement('li');
      li.textContent = lm;
      landmarksList.appendChild(li);
    });

    // Peers
    const peersList = document.getElementById('contemporary-peers-list');
    peersList.innerHTML = '';
    (sanctuary.contemporary_peers || []).forEach((cp) => {
      const li = document.createElement('li');
      li.textContent = cp;
      peersList.appendChild(li);
    });

    // Producers & Collaborators
    const producersContainer = document.getElementById('producers-container');
    producersContainer.innerHTML = '';
    (sanctuary.producers || []).forEach((prod) => {
      const item = document.createElement('div');
      item.className = 'producer-item';
      const relatedWorks = prod.with_queried_artist.length > 0 
        ? prod.with_queried_artist.join(', ')
        : (prod.with_related_artists || []).join(', ');

      item.innerHTML = `
        <div class="producer-header">
          <span class="producer-name">${escapeHtml(prod.name)}</span>
          <span class="producer-role">${escapeHtml(prod.role)}</span>
        </div>
        <p class="producer-works">Landmark Projects: ${escapeHtml(relatedWorks || 'Key studio collaborator')}</p>
      `;
      producersContainer.appendChild(item);
    });
  }

  // 4. Tab 3: Discography Timeline
  const timelineContainer = document.getElementById('discography-timeline-container');
  timelineContainer.innerHTML = '';
  document.getElementById('discography-summary-text').textContent = dossier.discography_summary || 'Studio Album Chronology';

  if (dossier.discography_context && dossier.discography_context.length > 0) {
    dossier.discography_context.forEach((entry) => {
      const card = document.createElement('div');
      card.className = `timeline-card-item ${entry.is_current ? 'current-album' : ''}`;
      const relLabel = entry.is_current ? '▶ CURRENT' : entry.relationship;
      const releaseYear = entry.release_date ? entry.release_date.substring(0, 4) : '—';

      card.innerHTML = `
        <div class="timeline-album-info">
          <span class="timeline-rel-badge">${escapeHtml(relLabel)}</span>
          <span class="timeline-album-title">${escapeHtml(entry.title)}</span>
          <span class="timeline-album-year">Released: ${escapeHtml(releaseYear)}</span>
        </div>
        <div class="timeline-rating-badge">
          ${escapeHtml(entry.allmusic_rating || '★★★★☆')}
        </div>
      `;
      timelineContainer.appendChild(card);
    });
  } else {
    timelineContainer.innerHTML = '<p class="timeline-hint">No discography chronology available.</p>';
  }

  // 5. Reset Chat for new song
  resetChatForSong(song);
}

/* =====================================================================
   AI CHAT SYSTEM
   ===================================================================== */
function initChatSystem() {
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const quickPromptBtns = document.querySelectorAll('.quick-prompt-btn');

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const prompt = input.value.trim();
    if (!prompt) return;

    sendChatMessage(prompt);
    input.value = '';
  });

  quickPromptBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      const prompt = btn.getAttribute('data-prompt');
      if (prompt) {
        sendChatMessage(prompt);
      }
    });
  });
}

function resetChatForSong(song) {
  chatHistory = [];
  const messagesScroll = document.getElementById('chat-messages-scroll');
  messagesScroll.innerHTML = `
    <div class="message assistant-message">
      <div class="msg-bubble">
        👋 Primed on <strong>"${escapeHtml(song.title)}"</strong> by <strong>${escapeHtml(song.artist)}</strong> from the album <em>"${escapeHtml(song.album || 'this album')}"</em>. What would you like to know about the creative spark, studio sanctuary, or session lore?
      </div>
    </div>
  `;
}

async function sendChatMessage(prompt) {
  if (!currentDossier || !currentDossier.song) {
    alert('Please select or search a song first.');
    return;
  }

  const messagesScroll = document.getElementById('chat-messages-scroll');

  // Append user bubble
  appendChatBubble('user', prompt);

  // Append temporary typing indicator
  const typingIndicator = document.createElement('div');
  typingIndicator.className = 'message assistant-message';
  typingIndicator.id = 'typing-indicator';
  typingIndicator.innerHTML = '<div class="msg-bubble"><em>Consulting studio archives &amp; dossier...</em></div>';
  messagesScroll.appendChild(typingIndicator);
  messagesScroll.scrollTop = messagesScroll.scrollHeight;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        artist: currentDossier.song.artist,
        song: currentDossier.song.title,
        prompt: prompt,
        history: chatHistory,
      }),
    });

    const data = await res.json();
    typingIndicator.remove();

    if (res.ok && data.reply) {
      appendChatBubble('assistant', data.reply);
      chatHistory.push({ role: 'user', content: prompt });
      chatHistory.push({ role: 'assistant', content: data.reply });
    } else {
      appendChatBubble('assistant', `⚠️ ${data.detail || 'Could not query AI musicologist.'}`);
    }
  } catch (err) {
    typingIndicator.remove();
    appendChatBubble('assistant', `⚠️ Network error: ${err.message}`);
  }
}

function appendChatBubble(role, text) {
  const messagesScroll = document.getElementById('chat-messages-scroll');
  const bubbleWrap = document.createElement('div');
  bubbleWrap.className = `message ${role}-message`;

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.textContent = text;

  bubbleWrap.appendChild(bubble);
  messagesScroll.appendChild(bubbleWrap);
  messagesScroll.scrollTop = messagesScroll.scrollHeight;
}

/* =====================================================================
   HELPERS & UTILITIES
   ===================================================================== */
function showLoading(show, message = 'Synthesizing Dossier...') {
  const overlay = document.getElementById('loading-overlay');
  const msgEl = document.getElementById('loading-headline');

  if (show) {
    msgEl.textContent = message;
    overlay.classList.remove('hidden');
  } else {
    overlay.classList.add('hidden');
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
