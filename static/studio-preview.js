(() => {
  'use strict';

  const style = document.createElement('style');
  style.textContent = `
    .mediaPreviewGrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
    .mediaPreviewCard{border:1px solid var(--line);border-radius:14px;padding:12px;background:#0b1018;min-width:0}
    .mediaPreviewCard video{display:block;width:100%;aspect-ratio:16/9;background:#030508;border-radius:10px;margin:10px 0;object-fit:contain}
    .mediaPreviewTitle{display:flex;justify-content:space-between;gap:10px;align-items:start}
    .mediaPreviewTitle strong{overflow-wrap:anywhere}
    .mediaPreviewKind{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--accent)}
    .mediaPreviewError{color:var(--bad);font-size:12px}
  `;
  document.head.appendChild(style);

  async function previewApi(path, options = {}) {
    const headers = {...(options.headers || {})};
    const bearer = localStorage.getItem('zmovie_token') || '';
    if (bearer) headers.Authorization = 'Bearer ' + bearer;
    const response = await fetch(path, {...options, headers});
    if (!response.ok) {
      let detail = '';
      try {
        const body = await response.json();
        detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail || body);
      } catch {
        detail = await response.text();
      }
      throw new Error(detail || `HTTP ${response.status}`);
    }
    return response.json();
  }

  function fileName(path) {
    return String(path || '').split(/[\\/]/).pop() || 'video.mp4';
  }

  function mediaDescription(asset) {
    const meta = asset.metadata || {};
    const parts = [];
    if (meta.codec) parts.push(String(meta.codec).toUpperCase());
    if (meta.width && meta.height) parts.push(`${meta.width}×${meta.height}`);
    if (meta.duration_seconds) parts.push(`${Number(meta.duration_seconds).toFixed(2)}s`);
    return parts.join(' · ');
  }

  function makeCard(asset, preview) {
    const card = document.createElement('div');
    card.className = 'mediaPreviewCard';

    const heading = document.createElement('div');
    heading.className = 'mediaPreviewTitle';
    const title = document.createElement('strong');
    title.textContent = asset.name || fileName(asset.path);
    const kind = document.createElement('span');
    kind.className = 'mediaPreviewKind';
    kind.textContent = asset.kind || 'asset';
    heading.append(title, kind);

    const video = document.createElement('video');
    video.controls = true;
    video.preload = 'metadata';
    video.playsInline = true;
    video.src = preview.url;
    video.setAttribute('aria-label', `Preview ${asset.name || fileName(asset.path)}`);

    const meta = document.createElement('div');
    meta.className = 'small';
    const description = mediaDescription(asset);
    meta.textContent = `${fileName(asset.path)}${description ? ' · ' + description : ''}`;

    const expiry = document.createElement('div');
    expiry.className = 'small';
    expiry.textContent = `Signed preview URL · ${Math.round((preview.expires_in || 0) / 60)} min`;

    const error = document.createElement('div');
    error.className = 'mediaPreviewError hidden';
    error.textContent = 'Preview failed or URL expired. Refresh this project to issue a new preview URL.';
    video.addEventListener('error', () => error.classList.remove('hidden'));

    card.append(heading, video, meta, expiry, error);
    return card;
  }

  async function loadMp4Previews(projectId, mount) {
    mount.textContent = 'Loading MP4 assets…';
    try {
      const data = await previewApi(`/api/v2/projects/${encodeURIComponent(projectId)}/assets`);
      const assets = (data.items || [])
        .filter(asset => String(asset.path || '').toLowerCase().endsWith('.mp4'))
        .sort((a, b) => {
          const rank = item => item.kind === 'final' ? 0 : item.kind === 'render' ? 1 : 2;
          return rank(a) - rank(b);
        });

      mount.replaceChildren();
      if (!assets.length) {
        const empty = document.createElement('p');
        empty.className = 'small';
        empty.textContent = 'No managed MP4 assets for this project yet.';
        mount.appendChild(empty);
        return;
      }

      const grid = document.createElement('div');
      grid.className = 'mediaPreviewGrid';
      mount.appendChild(grid);

      await Promise.all(assets.map(async asset => {
        try {
          const preview = await previewApi(
            `/api/v2/projects/${encodeURIComponent(projectId)}/assets/${encodeURIComponent(asset.id)}/preview`,
            {method: 'POST'}
          );
          grid.appendChild(makeCard(asset, preview));
        } catch (error) {
          const card = document.createElement('div');
          card.className = 'mediaPreviewCard';
          const title = document.createElement('strong');
          title.textContent = asset.name || fileName(asset.path);
          const message = document.createElement('div');
          message.className = 'mediaPreviewError';
          message.textContent = error.message;
          card.append(title, message);
          grid.appendChild(card);
        }
      }));
    } catch (error) {
      mount.textContent = '';
      const message = document.createElement('div');
      message.className = 'mediaPreviewError';
      message.textContent = `Unable to load MP4 previews: ${error.message}`;
      mount.appendChild(message);
    }
  }

  function install() {
    if (typeof window.renderDetail !== 'function' || window.renderDetail.__zmoviePreviewWrapped) return false;
    const original = window.renderDetail;
    const wrapped = function(data) {
      original(data);
      const projectId = data && data.project && data.project.id;
      const detail = document.getElementById('detail');
      if (!projectId || !detail) return;

      const section = document.createElement('div');
      section.id = 'mp4Previews';
      const heading = document.createElement('div');
      heading.className = 'row';
      const title = document.createElement('h3');
      title.style.flex = '3';
      title.textContent = 'MP4 Previews';
      const refresh = document.createElement('button');
      refresh.textContent = 'Refresh previews';
      const mount = document.createElement('div');
      heading.append(title, refresh);
      section.append(heading, mount);

      const ops = document.getElementById('ops');
      if (ops && ops.parentNode === detail) detail.insertBefore(section, ops);
      else detail.appendChild(section);

      refresh.addEventListener('click', () => loadMp4Previews(projectId, mount));
      loadMp4Previews(projectId, mount);
    };
    wrapped.__zmoviePreviewWrapped = true;
    window.renderDetail = wrapped;
    return true;
  }

  if (!install()) {
    const timer = setInterval(() => {
      if (install()) clearInterval(timer);
    }, 50);
    setTimeout(() => clearInterval(timer), 5000);
  }
})();
