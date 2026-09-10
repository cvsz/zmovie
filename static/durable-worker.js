(() => {
  'use strict';

  const STAGE_LABELS = {
    queued: 'Queued',
    claimed: 'Claimed',
    running: 'Rendering',
    render: 'Rendering',
    validate: 'Validating',
    assemble: 'Assembling',
    'prepare-bilibili': 'Preparing Bilibili',
    export: 'Exporting',
    'approval-gate': 'Approval required',
    retry_wait: 'Retry wait',
    recovery_required: 'Recovery required',
    failed: 'Failed',
    completed: 'Completed',
  };

  const style = document.createElement('style');
  style.textContent = `
    .durableRun{margin:16px 0;padding:14px;border:1px solid var(--line);border-radius:14px;background:#0b1018}
    .durableRunGrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:10px}
    .durableRunMetric{border:1px solid var(--line);border-radius:10px;padding:10px;background:#0d131d}
    .durableRunMetric span{display:block;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.08em}
    .durableRunMetric strong{display:block;margin-top:4px;overflow-wrap:anywhere}
    .durableState{font-size:12px;font-weight:800;color:var(--accent)}
    .durableError{color:var(--bad);white-space:pre-wrap;overflow-wrap:anywhere;margin-top:8px}
  `;
  document.head.appendChild(style);

  async function api(path) {
    const headers = {};
    const bearer = localStorage.getItem('zmovie_token') || '';
    if (bearer) headers.Authorization = 'Bearer ' + bearer;
    const response = await fetch(path, {headers});
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `HTTP ${response.status}`);
    return data;
  }

  function safe(value) {
    if (value === null || value === undefined || value === '') return '—';
    return String(value);
  }

  function label(run, worker) {
    const raw = String((worker && worker.status) || (run && run.stage) || (run && run.status) || 'idle');
    return STAGE_LABELS[raw] || raw.replaceAll('_', ' ');
  }

  function metric(name, value) {
    const node = document.createElement('div');
    node.className = 'durableRunMetric';
    const title = document.createElement('span');
    title.textContent = name;
    const detail = document.createElement('strong');
    detail.textContent = safe(value);
    node.append(title, detail);
    return node;
  }

  function renderState(mount, run) {
    mount.replaceChildren();
    const worker = run && run.worker ? run.worker : null;
    const heading = document.createElement('div');
    heading.className = 'row';
    const title = document.createElement('strong');
    title.textContent = 'Durable production';
    const state = document.createElement('span');
    state.className = 'durableState';
    state.textContent = run ? label(run, worker) : 'Idle';
    heading.append(title, state);
    mount.appendChild(heading);

    if (!run) {
      const note = document.createElement('p');
      note.className = 'small';
      note.textContent = 'No durable production run has been queued for this project.';
      mount.appendChild(note);
      return;
    }

    const grid = document.createElement('div');
    grid.className = 'durableRunGrid';
    grid.append(
      metric('Run ID', run.id),
      metric('Worker job', run.worker_job_id),
      metric('Provider', run.provider),
      metric('Attempt', worker ? `${Number(worker.attempts || 0) + 1}/${worker.max_attempts || 1}` : '—'),
      metric('Stage', run.stage),
      metric('Heartbeat', worker && worker.heartbeat_at ? worker.heartbeat_at : '—'),
    );
    mount.appendChild(grid);
    const error = safe((worker && (worker.error_message || worker.error_code)) || run.error);
    if (error !== '—') {
      const node = document.createElement('div');
      node.className = 'durableError';
      node.textContent = error;
      mount.appendChild(node);
    }
  }

  async function refresh(projectId, mount) {
    try {
      const data = await api(`/api/v2/projects/${encodeURIComponent(projectId)}/production/run`);
      renderState(mount, data.run || null);
    } catch (error) {
      mount.textContent = `Durable status unavailable: ${error.message}`;
    }
  }

  function install() {
    if (typeof window.renderDetail !== 'function' || window.renderDetail.__zmovieDurableWrapped) return false;
    const original = window.renderDetail;
    const wrapped = function(data) {
      original(data);
      const projectId = data && data.project && data.project.id;
      const detail = document.getElementById('detail');
      if (!projectId || !detail) return;
      const mount = document.createElement('section');
      mount.className = 'durableRun';
      detail.prepend(mount);
      refresh(projectId, mount);
      const timer = setInterval(() => {
        if (!mount.isConnected) {
          clearInterval(timer);
          return;
        }
        refresh(projectId, mount);
      }, 5000);
    };
    wrapped.__zmovieDurableWrapped = true;
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
