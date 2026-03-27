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
  const initials = username.slice(0, 2).toUpperCase();

  const nav = [
    { section: 'Overview', items: [
      ['home', '📊', 'Dashboard', '/frontend/pages/dashboard.html'],
    ]},
    { section: 'Network', items: [
      ['devices', '🖥️', 'Devices', '/frontend/pages/devices.html'],
      ['topology', '🔗', 'Topology', '/frontend/pages/topology.html'],
    ]},
    { section: 'Policy', items: [
      ['policy', '📋', 'Policies', '/frontend/pages/policies.html'],
      ['deploy', '🚀', 'Deployments', '/frontend/pages/deployment.html'],
    ]},
    { section: 'Assurance', items: [
      ['compliance', '🛡️', 'Compliance', '/frontend/pages/compliance.html'],
      ['telemetry', '📡', 'Telemetry', '/frontend/pages/telemetry.html'],
    ]},
    { section: 'System', items: [
      ['audit', '📝', 'Audit Logs', '/frontend/pages/audit.html'],
    ]},
  ];

  let navHTML = '';
  nav.forEach(group => {
    navHTML += `<div class="nav-section-title">${group.section}</div>`;
    group.items.forEach(([key, icon, label, href]) => {
      navHTML += `<a class="${key === activeKey ? 'active' : ''}" href="${href}">
        <span class="nav-icon">${icon}</span>
        <span>${label}</span>
      </a>`;
    });
  });

  document.body.innerHTML = `
    <div class="page-shell">
      <aside class="sidebar" id="sidebar">
        <div class="sidebar-brand">
          <a href="/frontend/pages/dashboard.html" class="logo">
            <div class="logo-icon">⚡</div>
            <div>
              <div class="logo-text">IBN Controller</div>
              <div class="logo-sub">Network Automation</div>
            </div>
          </a>
        </div>
        <nav class="sidebar-nav">
          ${navHTML}
        </nav>
        <div class="sidebar-user">
          <div class="user-avatar">${initials}</div>
          <div class="user-info">
            <div class="user-name">${username}</div>
            <div class="user-role">${role}</div>
          </div>
          <button id="logoutBtn" class="ghost" style="padding:6px 10px; font-size:11px;">Logout</button>
        </div>
      </aside>
      <div class="main-area">
        <header class="topbar">
          <h1>${pageTitle}</h1>
          <div class="topbar-actions">
            <button class="ghost" id="mobileMenuBtn" style="display:none;">☰ Menu</button>
          </div>
        </header>
        <main class="content" id="content"></main>
      </div>
    </div>
  `;

  document.getElementById('logoutBtn').addEventListener('click', () => {
    clearAuth();
    window.location.href = '/frontend/pages/login.html';
  });

  // Mobile menu toggle
  const menuBtn = document.getElementById('mobileMenuBtn');
  if (window.innerWidth <= 768) {
    menuBtn.style.display = 'inline-flex';
  }
  menuBtn.addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
  });
}

function showMessage(containerId, message, type = 'success') {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.style.display = 'block';
  el.className = `message ${type}`;
  el.textContent = message;
}

function formatDate(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  return d.toLocaleString('en-US', {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
    hour12: false
  });
}
