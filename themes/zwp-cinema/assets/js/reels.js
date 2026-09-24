/* ZeaZ Cinema: original mobile-first accessible reels. No TikSwipe source or assets. */
(() => {
  'use strict';
  const config = window.ZWPC;
  const feed = document.getElementById('zwpc-feed');
  if (!config || !feed) return;

  const status = document.getElementById('zwpc-status');
  const filter = document.getElementById('zwpc-genre');
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const motion = prefersReducedMotion ? 'instant' : 'smooth';
  let page = Number(feed.dataset.nextPage || 2);
  let hasMore = feed.dataset.hasMore === '1';
  let loading = false;
  let active = 0;
  let lastWheelAt = 0;
  let savedIds = new Set();
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting && entry.intersectionRatio >= 0.6) {
        const position = slides().indexOf(entry.target);
        if (position >= 0) {
          active = position;
          pauseInactive();
          if (position >= slides().length - 2 && hasMore) void loadMore();
        }
      }
    }
  }, { root: feed, threshold: [0, 0.6, 0.85] });

  function slides() { return Array.from(feed.querySelectorAll('.zwpc-reel')); }
  function announce(message) { if (status) status.textContent = message; }
  function pauseInactive() {
    slides().forEach((slide, index) => {
      const video = slide.querySelector('video');
      if (!video) return;
      if (index !== active || document.hidden) {
        video.pause();
      } else if (!prefersReducedMotion) {
        video.muted = true;
        video.play().catch(() => {});
      }
      const control = slide.querySelector('.zwpc-play');
      if (control) control.textContent = video.paused ? '▶' : 'Ⅱ';
    });
  }
  function navigate(amount) {
    const next = Math.max(0, Math.min(active + amount, slides().length - 1));
    const target = slides()[next];
    if (target) {
      active = next;
      feed.scrollTo({ top: target.offsetTop, behavior: motion });
      pauseInactive();
      if (next >= slides().length - 2 && hasMore) void loadMore();
    }
  }
  function setFavoriteIcon(slide, saved) {
    const button = slide.querySelector('.zwpc-favorite');
    if (!button) return;
    button.setAttribute('aria-pressed', String(saved));
    button.setAttribute('aria-label', saved ? config.unfavoriteLabel : config.favoriteLabel);
    button.textContent = saved ? '♥' : '♡';
  }
  async function api(path, options = {}) {
    const response = await fetch(config.api + path, {
      credentials: 'same-origin',
      headers: { 'X-WP-Nonce': config.nonce, ...(options.headers || {}) },
      ...options
    });
    if (!response.ok) throw new Error('Request failed: ' + response.status);
    return response.json();
  }
  async function refreshFavorites() {
    if (!config.loggedIn) return;
    try {
      savedIds = new Set((await api('favorites')).map(Number));
      slides().forEach(slide => setFavoriteIcon(slide, savedIds.has(Number(slide.dataset.filmId))));
    } catch {
      announce('Unable to load saved films.');
    }
  }
  async function toggleFavorite(slide) {
    if (!config.loggedIn) {
      window.location.assign(config.loginUrl);
      return;
    }
    const id = Number(slide.dataset.filmId);
    if (!Number.isSafeInteger(id) || id < 1) return;
    const button = slide.querySelector('.zwpc-favorite');
    if (button) button.disabled = true;
    try {
      const result = await api('favorites/' + id, { method: 'POST' });
      if (result.saved) savedIds.add(id);
      else savedIds.delete(id);
      slides().filter(item => Number(item.dataset.filmId) === id)
        .forEach(item => setFavoriteIcon(item, result.saved));
    } catch {
      announce('Saving this film failed. Please try again.');
    } finally {
      if (button) button.disabled = false;
    }
  }
  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = String(text);
    return node;
  }
  function validUrl(raw, video = false) {
    try {
      const url = new URL(raw);
      if (url.protocol !== 'https:') return '';
      if (video && !/\\.(mp4|webm)$/i.test(url.pathname)) return '';
      return url.href;
    } catch { return ''; }
  }
  function makeSlide(item) {
    const slide = element('article', 'zwpc-reel');
    slide.tabIndex = 0;
    slide.dataset.filmId = String(item.id);
    const media = element('div', 'zwpc-reel-media');
    const videoUrl = validUrl(item.video, true);
    const poster = validUrl(item.poster);
    if (videoUrl) {
      const video = element('video');
      video.setAttribute('playsinline', '');
      video.muted = true;
      video.loop = true;
      video.preload = 'none';
      if (poster) video.poster = poster;
      const source = element('source');
      source.src = videoUrl;
      source.type = /\\.webm(?:\\?|$)/i.test(videoUrl) ? 'video/webm' : 'video/mp4';
      video.append(source);
      media.append(video);
    } else if (poster) {
      const image = element('img');
      image.src = poster;
      image.alt = String(item.title || '');
      image.loading = 'lazy';
      media.append(image);
    }
    media.append(element('div', 'zwpc-shade'));
    const copy = element('div', 'zwpc-reel-text');
    copy.append(element('p', 'zwpc-eyebrow', (item.genres || []).join(' / ')));
    const title = element('h2');
    const permalink = validUrl(item.url);
    const titleLink = element('a', '', item.title);
    if (permalink) titleLink.href = permalink;
    title.append(titleLink);
    copy.append(title);
    copy.append(element('p', '', item.excerpt || ''));
    copy.append(element('span', '', item.creator || ''));
    const details = element('a', 'zwpc-details-link', 'View film details ↗');
    if (permalink) details.href = permalink;
    copy.append(details);
    const actions = element('div', 'zwpc-reel-actions');
    const play = element('button', 'zwpc-play', '▶');
    play.type = 'button';
    play.setAttribute('aria-label', 'Play or pause trailer');
    const favorite = element('button', 'zwpc-favorite', '♡');
    favorite.type = 'button';
    favorite.setAttribute('aria-pressed', 'false');
    favorite.setAttribute('aria-label', config.favoriteLabel);
    actions.append(play, favorite);
    slide.append(media, copy, actions);
    setFavoriteIcon(slide, savedIds.has(Number(item.id)));
    return slide;
  }
  async function loadMore(reset = false) {
    if (loading || (!hasMore && !reset)) return;
    loading = true;
    announce(config.moreLabel);
    const requested = reset ? 1 : page;
    const genre = filter && filter.value ? '&genre=' + encodeURIComponent(filter.value) : '';
    try {
      const result = await api('feed?page=' + requested + genre);
      if (reset) {
        observer.disconnect();
        feed.replaceChildren();
        active = 0;
      }
      for (const item of result.items || []) {
        const slide = makeSlide(item);
        feed.append(slide);
        observer.observe(slide);
      }
      page = requested + 1;
      hasMore = Boolean(result.has_more);
      announce(slides().length ? '' : config.emptyLabel);
      if (reset) {
        feed.scrollTop = 0;
        pauseInactive();
      }
    } catch {
      announce('Could not load films. Check your connection and try again.');
    } finally {
      loading = false;
    }
  }

  feed.addEventListener('click', event => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    const slide = target.closest('.zwpc-reel');
    if (!slide) return;
    if (target.closest('.zwpc-favorite')) void toggleFavorite(slide);
    if (target.closest('.zwpc-play')) {
      const video = slide.querySelector('video');
      if (!video) return;
      if (video.paused) video.play().catch(() => announce('Unable to play trailer.'));
      else video.pause();
      target.textContent = video.paused ? '▶' : 'Ⅱ';
    }
  });
  feed.addEventListener('wheel', event => {
    if (Math.abs(event.deltaY) < 8) return;
    event.preventDefault();
    const now = Date.now();
    if (now - lastWheelAt < 580) return;
    lastWheelAt = now;
    navigate(event.deltaY > 0 ? 1 : -1);
  }, { passive: false });
  document.addEventListener('keydown', event => {
    if (event.altKey || event.ctrlKey || event.metaKey ||
        /^(INPUT|SELECT|TEXTAREA|BUTTON)$/.test(document.activeElement?.tagName || '')) return;
    const focusedInFeed = feed.contains(document.activeElement) || document.activeElement === document.body;
    if (!focusedInFeed) return;
    if (['ArrowDown', 'ArrowRight'].includes(event.key)) { event.preventDefault(); navigate(1); }
    if (['ArrowUp', 'ArrowLeft'].includes(event.key)) { event.preventDefault(); navigate(-1); }
  });
  document.getElementById('zwpc-prev')?.addEventListener('click', () => navigate(-1));
  document.getElementById('zwpc-next')?.addEventListener('click', () => navigate(1));
  filter?.addEventListener('change', () => { void loadMore(true); });
  document.addEventListener('visibilitychange', pauseInactive);
  slides().forEach(slide => observer.observe(slide));
  void refreshFavorites();
})();
