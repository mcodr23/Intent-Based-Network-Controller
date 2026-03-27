const API_BASE = '/api';

function getToken() {
  return localStorage.getItem('ibn_token');
}

function setAuth(data) {
  localStorage.setItem('ibn_token', data.access_token);
  localStorage.setItem('ibn_user', JSON.stringify(data.user));
}

function getUser() {
  const raw = localStorage.getItem('ibn_user');
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch (e) {
    return null;
  }
}

function clearAuth() {
  localStorage.removeItem('ibn_token');
  localStorage.removeItem('ibn_user');
}

function requireAuth() {
  if (!getToken()) {
    window.location.href = '/frontend/pages/login.html';
    return false;
  }
  return true;
}

async function apiFetch(path, options = {}) {
  const headers = options.headers || {};
  headers['Content-Type'] = 'application/json';

  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    clearAuth();
    window.location.href = '/frontend/pages/login.html';
    throw new Error('Session expired. Please login again.');
  }

  let data = null;
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const message = data?.detail || data?.message || `Request failed (${response.status})`;
    throw new Error(message);
  }

  return data;
}

function renderShell(pageTitle, activeKey) {
  const user = getUser();
  const role = user?.role?.name || 'Unknown';
  const username = user?.username || 'anonymous';
  const nav = [
    ['home', 'Dashboard', '/frontend/pages/dashboard.html'],
    ['devices', 'Devices', '/frontend/pages/devices.html'],
    ['topology', 'Topology', '/frontend/pages/topology.html'],
    ['policy', 'Policies', '/frontend/pages/policies.html'],
    ['deploy', 'Deployments', '/frontend/pages/deployment.html'],
    ['compliance', 'Compliance', '/frontend/pages/compliance.html'],
    ['telemetry', 'Telemetry', '/frontend/pages/telemetry.html'],
    ['audit', 'Audit', '/frontend/pages/audit.html'],
  ];

  const links = nav
    .map(
      ([key, label, href]) => `<a class="${key === activeKey ? 'active' : ''}" href="${href}">${label}</a>`
    )
    .join('');

  document.body.innerHTML = `
    <div class="page-shell">
      <div class="topbar">
        <div>
          <div class="brand">Intent-Based Network Controller</div>
          <div class="small">${pageTitle}</div>
        </div>
        <div class="nav-links">${links}</div>
        <div class="small">${username} (${role}) <button id="logoutBtn" class="ghost" style="margin-left:8px;">Logout</button></div>
      </div>
      <main class="content" id="content"></main>
    </div>
  `;

  document.getElementById('logoutBtn').addEventListener('click', () => {
    clearAuth();
    window.location.href = '/frontend/pages/login.html';
  });
}

function showMessage(containerId, message, type = 'success') {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.className = `message ${type}`;
  el.textContent = message;
}

function formatDate(ts) {
  if (!ts) return '-';
  const d = new Date(ts);
  return d.toLocaleString();
}
