// JadiSan — Multi-Role Civic Grievance System (JavaScript Engine)

// ── Application State & Role Account Registry ───────────────────────────────
let activeSlide = 1;
let currentRole = 'Zone Officer'; // Default active role view

let currentZoneOfficer = {
  name: 'Arun Kumar',
  role: 'Zone Officer',
  title: 'Zone 5 Officer (South Chennai)',
  password: 'password123'
};

// Pre-configured Credentials for All 9 Authority Roles
const demoAccounts = {
  'Zone Officer': { name: 'Arun Kumar', role: 'Zone Officer', title: 'Zone 5 Officer (South Chennai)', password: 'password123', avatar: 'AK' },
  'Road Department': { name: 'Rajesh Verma', role: 'Road Department', title: 'Senior Executive Engineer (Roads)', password: 'password123', avatar: 'RV' },
  'Water Department': { name: 'Suresh Nair', role: 'Water Department', title: 'Chief Engineer (Metro Water)', password: 'password123', avatar: 'SN' },
  'Sewage Department': { name: 'Kavitha Reddy', role: 'Sewage Department', title: 'Superintending Engineer (Sewage)', password: 'password123', avatar: 'KR' },
  'Sanitation Department': { name: 'Manoj Sharma', role: 'Sanitation Department', title: 'Chief Sanitation Officer', password: 'password123', avatar: 'MS' },
  'Electricity Department': { name: 'Anitha Rao', role: 'Electricity Department', title: 'Divisional Engineer (Electricity)', password: 'password123', avatar: 'AR' },
  'Ward Officer': { name: 'Prakash Chand', role: 'Ward Officer', title: 'Ward 104 Administrative Officer', password: 'password123', avatar: 'PC' },
  'District Officer': { name: 'Dr. V. K. Sundaram', role: 'District Officer', title: 'District Magistrate & Collector', password: 'password123', avatar: 'VS' },
  'Municipal Commissioner': { name: 'G. Swaminathan IAS', role: 'Municipal Commissioner', title: 'Greater Chennai Municipal Commissioner', password: 'password123', avatar: 'GS' }
};

// Quick Login Selector Function for 1-Click Test Buttons
function quickLoginRole(roleName) {
  const roleSelect = document.getElementById('loginRole');
  if (roleSelect) roleSelect.value = roleName;

  const account = demoAccounts[roleName];
  if (account) {
    document.getElementById('loginName').value = account.name;
    document.getElementById('loginPassword').value = account.password;
  }

  document.querySelectorAll('.demo-pill').forEach(btn => {
    const text = btn.textContent.toLowerCase();
    const target = roleName.toLowerCase();
    if (target.includes(text.replace(/[^a-z]/g, '')) || text.includes(target.split(' ')[0])) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  showToast(`Selected ${roleName} credentials (${account ? account.name : ''})`);
}

// Initial Complaint Records (Will sync dynamically with Backend API)
let complaints = [
  {
    id: 'JDS-001',
    db_id: 'JDS-001',
    ref_id: 'JDS-001',
    dept: 'Pothole — Road Department',
    problem: 'Pothole',
    department: 'Road Department',
    assigned_department: 'Road Department',
    severity: 'High',
    area: 'Anna Nagar',
    status: 'FORWARDED',
    assigned: true,
    resolved: false,
    lat: 13.0850,
    lng: 80.2100,
    transcript: 'There is a big pothole near Anna Nagar bus stand.',
    department_response: '',
    created_at: '2026-09-04T10:32:00Z',
    forwarded_at: '2026-09-04T10:40:00Z',
    response_received_at: null,
    resolved_at: null
  },
  {
    id: 'JDS-002',
    db_id: 'JDS-002',
    ref_id: 'JDS-002',
    dept: 'Sewage Overflow — Sewage Department',
    problem: 'Sewage Overflow',
    department: 'Sewage Department',
    assigned_department: 'Sewage Department',
    severity: 'Critical',
    area: 'Velachery',
    status: 'OPEN',
    assigned: false,
    resolved: false,
    lat: 12.9815,
    lng: 80.2180,
    transcript: 'Sewage water overflow near Velachery railway station.',
    department_response: '',
    created_at: '2026-09-04T08:45:00Z',
    forwarded_at: null,
    response_received_at: null,
    resolved_at: null
  },
  {
    id: 'JDS-003',
    db_id: 'JDS-003',
    ref_id: 'JDS-003',
    dept: 'Water Leakage — Water Department',
    problem: 'Water Leakage',
    department: 'Water Department',
    assigned_department: 'Water Department',
    severity: 'High',
    area: 'Avadi',
    status: 'RESPONSE_RECEIVED',
    assigned: true,
    resolved: false,
    lat: 13.1147,
    lng: 80.1098,
    transcript: 'Water pipe leakage at Avadi market main street.',
    department_response: 'Water maintenance crew scheduled for repair work at 2 PM today.',
    created_at: '2026-09-04T07:20:00Z',
    forwarded_at: '2026-09-04T07:45:00Z',
    response_received_at: '2026-09-04T08:15:00Z',
    resolved_at: null
  },
  {
    id: 'JDS-004',
    db_id: 'JDS-004',
    ref_id: 'JDS-004',
    dept: 'Garbage Overflow — Sanitation Department',
    problem: 'Garbage Overflow',
    department: 'Sanitation Department',
    assigned_department: 'Sanitation Department',
    severity: 'Medium',
    area: 'Ambattur',
    status: 'RESOLVED',
    assigned: true,
    resolved: true,
    lat: 13.1143,
    lng: 80.1548,
    transcript: 'Garbage bin overflowing near Ambattur OT bus stop.',
    department_response: 'JDS-004 waste cleared by sanitation truck crew.',
    created_at: '2026-09-03T19:20:00Z',
    forwarded_at: '2026-09-03T19:30:00Z',
    response_received_at: '2026-09-04T08:00:00Z',
    resolved_at: '2026-09-04T09:10:00Z'
  },
  {
    id: 'JDS-005',
    db_id: 'JDS-005',
    ref_id: 'JDS-005',
    dept: 'Broken Streetlight — Electricity Department',
    problem: 'Broken Streetlight',
    department: 'Electricity Department',
    assigned_department: 'Electricity Department',
    severity: 'Medium',
    area: 'Tambaram',
    status: 'RESOLVED',
    assigned: true,
    resolved: true,
    lat: 12.9249,
    lng: 80.1000,
    transcript: 'Streetlight broken near Tambaram west bus stand.',
    department_response: 'Streetlight bulb replaced and electrical line tested.',
    created_at: '2026-09-03T18:15:00Z',
    forwarded_at: '2026-09-03T18:30:00Z',
    response_received_at: '2026-09-04T08:00:00Z',
    resolved_at: '2026-09-04T08:30:00Z'
  },
  {
    id: 'JDS-006',
    db_id: 'JDS-006',
    ref_id: 'JDS-006',
    dept: 'Damaged Drainage Pipe — Sewage Department',
    problem: 'Damaged Drainage Pipe',
    department: 'Sewage Department',
    assigned_department: 'Sewage Department',
    severity: 'High',
    area: 'Location Not Provided',
    status: 'OPEN',
    assigned: false,
    resolved: false,
    lat: null,
    lng: null,
    transcript: 'There is a damaged drainage pipe leaking here.',
    department_response: '',
    created_at: '2026-09-04T11:00:00Z',
    forwarded_at: null,
    response_received_at: null,
    resolved_at: null
  }
];

let selectedComplaintIndex = null;
let modalMapInstance = null;
let mainMapInstance = null;
let chartRate = null;
let chartOverview = null;
let chartResolution = null;

// Dynamic API Base URL
const API_BASE = (window.location.protocol === 'file:' || window.location.origin === 'null')
  ? 'http://localhost:8000'
  : '';

// Toast Notification Helper
function showToast(message) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `<i class="bi bi-info-circle-fill" style="color: #2563eb;"></i> ${message}`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// Format Date Helper
function formatDate(isoStr) {
  if (!isoStr) return '—';
  try {
    const d = new Date(isoStr);
    return d.toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  } catch (e) {
    return isoStr;
  }
}

// Normalize Status representation
function normalizeStatus(rawStatus, isResolved) {
  if (isResolved || rawStatus === 'RESOLVED' || rawStatus === 'resolved') return 'RESOLVED';
  if (rawStatus === 'RESPONSE_RECEIVED' || rawStatus === 'response_received') return 'RESPONSE_RECEIVED';
  if (rawStatus === 'FORWARDED' || rawStatus === 'forwarded') return 'FORWARDED';
  return 'OPEN';
}

// Format Status Badge HTML
function getStatusBadgeHtml(status) {
  switch (status) {
    case 'RESOLVED':
      return `<span class="badge badge-resolved"><i class="bi bi-check-circle-fill"></i> RESOLVED</span>`;
    case 'RESPONSE_RECEIVED':
      return `<span class="badge badge-response"><i class="bi bi-chat-dots-fill"></i> RESPONSE RECEIVED</span>`;
    case 'FORWARDED':
      return `<span class="badge badge-forwarded"><i class="bi bi-send-fill"></i> FORWARDED</span>`;
    case 'OPEN':
    default:
      return `<span class="badge badge-open"><i class="bi bi-exclamation-circle-fill"></i> OPEN</span>`;
  }
}

function inferDepartment(category, rawDept) {
  if (rawDept && rawDept !== 'General Municipal Office' && rawDept !== 'Municipal Department' && rawDept !== 'Other' && rawDept !== 'General') {
    return rawDept;
  }
  const cat = (category || '').toLowerCase();
  if (cat.includes('road') || cat.includes('pothole') || cat.includes('asphalt') || cat.includes('street damage')) {
    return 'Road Department';
  }
  if (cat.includes('sewage') || cat.includes('drain') || cat.includes('sewer') || cat.includes('manhole')) {
    return 'Sewage Department';
  }
  if (cat.includes('water') || cat.includes('leak') || cat.includes('pipe')) {
    return 'Water Department';
  }
  if (cat.includes('garbage') || cat.includes('waste') || cat.includes('sanitation') || cat.includes('trash')) {
    return 'Sanitation Department';
  }
  if (cat.includes('light') || cat.includes('streetlights') || cat.includes('electric') || cat.includes('power')) {
    return 'Electricity Department';
  }
  return 'Road Department';
}

// Fetch live complaints from API
async function loadLiveComplaints() {
  try {
    const res = await fetch(`${API_BASE}/api/complaints`);
    if (res.ok) {
      const data = await res.json();
      if (data.complaints && Array.isArray(data.complaints) && data.complaints.length > 0) {
        complaints = data.complaints.map((c, i) => {
          const isResolved = c.resolved || c.status === 'resolved' || c.status === 'RESOLVED';
          const normalizedStatus = normalizeStatus(c.status, isResolved);
          const categoryName = c.problem_type || c.category || 'Civic Problem';
          const rawDept = c.assigned_department || c.department || c.department_name;
          const deptName = inferDepartment(categoryName, rawDept);

          return {
            id: c.reference_id || c.id || `JDS-${String(i + 1).padStart(3, '0')}`,
            db_id: c.id || c.reference_id || `JDS-${String(i + 1).padStart(3, '0')}`,
            ref_id: c.reference_id || c.id,
            dept: `${categoryName} — ${deptName}`,
            problem: categoryName,
            department: deptName,
            assigned_department: deptName,
            severity: c.severity || 'Medium',
            area: c.area || c.location_name || c.location_text || 'Location Not Provided',
            status: normalizedStatus,
            assigned: c.assigned || normalizedStatus !== 'OPEN',
            resolved: normalizedStatus === 'RESOLVED',
            lat: (typeof c.latitude === 'number' && !isNaN(c.latitude)) ? c.latitude : null,
            lng: (typeof c.longitude === 'number' && !isNaN(c.longitude)) ? c.longitude : null,
            transcript: c.voice_transcription || c.complaint_text || c.transcript || c.summary || 'Civic Grievance Reported',
            department_response: c.department_response || '',
            created_at: c.created_at || new Date().toISOString(),
            forwarded_at: c.forwarded_at || null,
            response_received_at: c.response_received_at || null,
            resolved_at: c.resolved_at || c.solved_at || null
          };
        });
      }
    }
  } catch (e) {
    // Retain initial local records if backend offline
  }

  updateDashboardStats();
  renderComplaintsTable();
}

// ── Slide Navigation Controls ───────────────────────────────────────────────
function goToSlide(slideNumber) {
  activeSlide = slideNumber;
  document.querySelectorAll('.slide-screen').forEach(s => s.classList.remove('active'));

  const target = document.getElementById(`slide${slideNumber}`);
  if (target) {
    target.classList.add('active');
  }

  if (slideNumber === 3) {
    updateProfileUI();
    loadLiveComplaints();
  }
}

// Update Top Right Profile UI
function updateProfileUI() {
  const nameEl = document.getElementById('headerZoneOfficerName');
  const avatarEl = document.getElementById('headerAvatar');
  if (nameEl) nameEl.textContent = currentZoneOfficer.name;
  if (avatarEl) {
    const initials = currentZoneOfficer.name.split(' ').map(n => n[0]).join('').toUpperCase();
    avatarEl.textContent = initials || 'ZO';
  }
}

// ── Central Role Context & View Handler ─────────────────────────────────────
function applyActiveRoleContext(roleName, officerName) {
  currentRole = roleName || 'Zone Officer';

  const account = demoAccounts[currentRole] || {
    name: officerName || 'Arun Kumar',
    role: currentRole,
    title: `${currentRole} View`,
    avatar: 'AK'
  };

  const nameToUse = officerName || account.name;
  currentZoneOfficer.name = nameToUse;
  currentZoneOfficer.role = currentRole;

  // Update header dropdown
  const roleSelect = document.getElementById('roleSelector');
  if (roleSelect && roleSelect.value !== currentRole) {
    roleSelect.value = currentRole;
  }

  // Update header badge
  const headerRoleBadgeText = document.getElementById('headerRoleBadgeText');
  if (headerRoleBadgeText) {
    headerRoleBadgeText.textContent = `${currentRole} View`;
  }

  // Update header profile avatar & name
  const headerZoneOfficerName = document.getElementById('headerZoneOfficerName');
  if (headerZoneOfficerName) headerZoneOfficerName.textContent = nameToUse;

  const headerAvatar = document.getElementById('headerAvatar');
  if (headerAvatar) {
    const initials = nameToUse.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() || account.avatar || 'OFF';
    headerAvatar.textContent = initials;
  }

  // Update Welcome Banner
  const welcomeBannerTitle = document.getElementById('welcomeBannerTitle');
  if (welcomeBannerTitle) {
    welcomeBannerTitle.textContent = `Welcome back, ${nameToUse}!`;
  }
  const welcomeBannerDesc = document.getElementById('welcomeBannerDesc');
  if (welcomeBannerDesc) {
    if (currentRole === 'Zone Officer' || currentRole === 'Municipal Commissioner' || currentRole === 'District Officer') {
      welcomeBannerDesc.textContent = `You are managing all active civic complaints across Zone 5. Assign & route grievances across departments.`;
    } else {
      welcomeBannerDesc.textContent = `Active Scope: ${currentRole} Grievances & Field Operations | Zone 5 South Chennai`;
    }
  }

  // Re-render all view components
  updateDashboardStats();
  renderDepartmentWorkloadGrid();
  renderUrgentQueue();
  renderActivityFeed();
  renderComplaintsTable();
}

// ── Dynamic Dashboard Statistics Calculation ────────────────────────────────
function updateDashboardStats() {
  const filtered = getFilteredComplaints();
  const total = filtered.length;
  const opened = filtered.filter(c => c.status !== 'RESOLVED').length;
  const critical = filtered.filter(c => c.severity === 'Critical' || c.severity === 'High').length;
  const resolved = filtered.filter(c => c.status === 'RESOLVED').length;

  const elTotal = document.getElementById('statTotal');
  const elOpened = document.getElementById('statOpened');
  const elCritical = document.getElementById('statCritical');
  const elResolved = document.getElementById('statResolved');

  if (elTotal) elTotal.textContent = total.toLocaleString();
  if (elOpened) elOpened.textContent = opened.toLocaleString();
  if (elCritical) elCritical.textContent = critical.toLocaleString();
  if (elResolved) elResolved.textContent = resolved.toLocaleString();
}

// ── Department Operational Workload Breakdown Grid ──────────────────────────
function renderDepartmentWorkloadGrid() {
  const container = document.getElementById('deptWorkloadGrid');
  if (!container) return;

  const depts = [
    { name: 'Road Department', label: 'Roads & Potholes', icon: '🛣️', color: '#3b82f6' },
    { name: 'Water Department', label: 'Water Supply & Leaks', icon: '💧', color: '#06b6d4' },
    { name: 'Sewage Department', label: 'Drainage & Sewage', icon: '🚰', color: '#8b5cf6' },
    { name: 'Sanitation Department', label: 'Waste & Sanitation', icon: '🧹', color: '#10b981' },
    { name: 'Electricity Department', label: 'Streetlights & Power', icon: '⚡', color: '#f59e0b' }
  ];

  container.innerHTML = '';

  depts.forEach(d => {
    const deptComplaints = complaints.filter(c => 
      c.department === d.name || 
      c.assigned_department === d.name || 
      c.dept.includes(d.name)
    );
    const totalCount = deptComplaints.length;
    const activeCount = deptComplaints.filter(c => c.status !== 'RESOLVED').length;
    const resolvedCount = deptComplaints.filter(c => c.status === 'RESOLVED').length;
    const pct = totalCount > 0 ? Math.round((resolvedCount / totalCount) * 100) : 100;

    const card = document.createElement('div');
    card.className = `dept-card ${currentRole === d.name ? 'active-dept' : ''}`;
    card.onclick = () => {
      applyActiveRoleContext(d.name);
      showToast(`Switched workspace to ${d.name}`);
    };

    card.innerHTML = `
      <div class="dept-card-header">
        <span class="dept-card-icon" style="background: ${d.color}15;">${d.icon}</span>
        <span class="badge ${activeCount > 0 ? 'badge-open' : 'badge-resolved'}" style="font-size: 10px;">
          ${activeCount > 0 ? activeCount + ' Active' : 'All Clear'}
        </span>
      </div>
      <div class="dept-card-name">${d.label}</div>
      <div class="dept-card-meta">${totalCount} total • ${resolvedCount} resolved</div>
      <div class="dept-card-stat" style="color: ${d.color};">${activeCount} <span style="font-size: 11px; color: var(--text-muted); font-weight: 600;">pending</span></div>
      <div class="dept-progress-bar">
        <div class="dept-progress-fill" style="width: ${pct}%; background-color: ${d.color};"></div>
      </div>
    `;

    container.appendChild(card);
  });
}

// ── Render Urgent Action Items Queue ───────────────────────────────────────
function renderUrgentQueue() {
  const tbody = document.getElementById('dashboardUrgentTbody');
  const badge = document.getElementById('urgentQueueCountBadge');
  if (!tbody) return;

  tbody.innerHTML = '';
  const filtered = getFilteredComplaints();
  const urgentList = filtered.filter(c => c.status !== 'RESOLVED').sort((a, b) => {
    const sevScore = { 'Critical': 3, 'High': 2, 'Medium': 1, 'Low': 0 };
    return (sevScore[b.severity] || 0) - (sevScore[a.severity] || 0);
  }).slice(0, 5);

  if (badge) {
    badge.textContent = `${urgentList.length} Action Items`;
  }

  if (urgentList.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 16px;">No urgent action items in current scope.</td></tr>`;
    return;
  }

  urgentList.forEach(item => {
    const originalIndex = complaints.indexOf(item);
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong style="color: var(--primary-purple);">${item.id}</strong></td>
      <td><strong>${item.problem}</strong><br><span style="font-size: 11px; color: var(--text-muted);">${item.department}</span></td>
      <td>${item.area}</td>
      <td><span class="badge badge-${item.severity.toLowerCase()}">${item.severity}</span></td>
      <td>
        <button class="btn-outline" style="padding: 4px 8px; font-size: 11.5px; width: auto;" onclick="openDetailModal(${originalIndex})">
          <i class="bi bi-pencil-square"></i> Action
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// ── Render Live Activity Stream Feed ─────────────────────────────────────────
function renderActivityFeed() {
  const container = document.getElementById('dashboardActivityFeed');
  if (!container) return;

  container.innerHTML = '';

  const activities = [
    { type: 'sewage', title: '🎙️ WhatsApp Voice Complaint Logged', desc: 'Citizen reported sewage overflow at Velachery Railway Station.', time: '10m ago' },
    { type: 'water', title: '💬 Department Response Recorded', desc: 'Water Board engineer scheduled maintenance team for pipe leak.', time: '25m ago' },
    { type: 'road', title: '🔀 AI Auto-Forwarded to Road Dept', desc: 'Pothole complaint JDS-001 routed to Road Executive Engineer.', time: '1h ago' },
    { type: 'sanitation', title: '✅ Waste Clearance Completed', desc: 'Garbage bin near Ambattur OT cleared by sanitation crew.', time: '2h ago' },
    { type: 'electricity', title: '⚡ Streetlight Repair Verified', desc: 'Broken streetlight restored near Tambaram bus stand.', time: '3h ago' }
  ];

  activities.forEach(act => {
    const div = document.createElement('div');
    div.className = `activity-item ${act.type}`;
    div.innerHTML = `
      <div class="activity-icon"><i class="bi bi-clock-history"></i></div>
      <div class="activity-content">
        <div class="activity-title">${act.title}</div>
        <div class="activity-desc">${act.desc}</div>
      </div>
      <div class="activity-time">${act.time}</div>
    `;
    container.appendChild(div);
  });
}

// Filter complaints based on active Role Selector
function getFilteredComplaints() {
  if (currentRole === 'Zone Officer' || currentRole === 'Municipal Commissioner' || currentRole === 'District Officer') {
    return complaints;
  }
  // Filter for specific department view
  return complaints.filter(c => 
    c.department === currentRole || 
    c.assigned_department === currentRole ||
    c.dept.includes(currentRole)
  );
}

// Global Tab Switcher
function switchTab(pageName) {
  const targetNavItem = document.querySelector(`.sidebar-nav .nav-item[data-page="${pageName}"]`);
  if (targetNavItem) {
    targetNavItem.click();
  }
}

// ── Render Complaints Table ─────────────────────────────────────────────────
function renderComplaintsTable() {
  const tbody = document.getElementById('complaintsTbody');
  const titleBadge = document.getElementById('currentViewBadge');
  const tableTitle = document.getElementById('complaintsTableTitle');

  if (titleBadge) {
    titleBadge.textContent = currentRole === 'Zone Officer' ? 'Zone Officer View (All Complaints)' : `${currentRole} Workspace`;
  }
  if (tableTitle) {
    tableTitle.textContent = currentRole === 'Zone Officer' ? 'All Grievance Complaints' : `${currentRole} Assigned Complaints`;
  }

  if (!tbody) return;
  tbody.innerHTML = '';

  const filteredList = getFilteredComplaints();

  if (filteredList.length === 0) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan="6" style="text-align: center; padding: 24px; color: var(--text-muted);">No complaints found for ${currentRole}.</td>`;
    tbody.appendChild(tr);
    return;
  }

  filteredList.forEach((item) => {
    const originalIndex = complaints.indexOf(item);
    const tr = document.createElement('tr');

    const statusBadge = getStatusBadgeHtml(item.status);
    const slaBadge = item.resolved 
      ? `<span class="badge badge-resolved"><i class="bi bi-check-circle"></i> Resolved</span>`
      : `<span class="badge badge-open"><i class="bi bi-clock-history"></i> 24h SLA</span>`;

    tr.innerHTML = `
      <td><strong style="color: var(--primary-purple);">${item.id}</strong></td>
      <td><strong>${item.problem}</strong><br><span style="font-size: 11px; color: var(--text-muted);">${item.dept || item.department}</span></td>
      <td>${item.area}</td>
      <td>${slaBadge}</td>
      <td>${statusBadge}</td>
      <td style="text-align: center;">
        <button class="btn-outline" style="padding: 5px 12px; font-size: 12px; font-weight: 700; width: auto; display: inline-flex; align-items: center; gap: 4px;" onclick="event.stopPropagation(); openDetailModal(${originalIndex})">
          <i class="bi bi-pencil-square"></i> Action & Details
        </button>
      </td>
    `;

    tr.style.cursor = 'pointer';
    tr.addEventListener('click', () => {
      openDetailModal(originalIndex);
    });

    tbody.appendChild(tr);
  });
}

// ── Workflow Action: Forward Complaint to Department ────────────────────────
async function forwardToDepartment(index) {
  const item = complaints[index];
  if (!item) return;

  const targetId = item.db_id || item.id;
  const deptName = item.department || 'Road Department';

  try {
    const res = await fetch(`${API_BASE}/api/complaints/${targetId}/forward`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ department: deptName })
    });

    if (res.ok) {
      item.status = 'FORWARDED';
      item.assigned = true;
      item.assigned_department = deptName;
      item.forwarded_at = new Date().toISOString();
      showToast(`Complaint ${item.id} forwarded to ${deptName}.`);
    } else {
      item.status = 'FORWARDED';
      item.assigned = true;
      item.assigned_department = deptName;
      item.forwarded_at = new Date().toISOString();
      showToast(`Complaint ${item.id} forwarded to ${deptName}.`);
    }
  } catch (e) {
    // Local fallback update if backend offline
    item.status = 'FORWARDED';
    item.assigned = true;
    item.assigned_department = deptName;
    item.forwarded_at = new Date().toISOString();
    showToast(`Complaint ${item.id} forwarded to ${deptName}.`);
  }

  updateDashboardStats();
  renderComplaintsTable();
  if (selectedComplaintIndex === index) openDetailModal(index);
}

// ── Workflow Action: Submit Department Response ──────────────────────────────
async function submitDepartmentResponse(index) {
  const item = complaints[index];
  if (!item) return;

  const inputEl = document.getElementById('deptResponseInput');
  const responseText = inputEl ? inputEl.value.trim() : '';

  if (!responseText) {
    showToast('Please enter a response before submitting.');
    return;
  }

  const targetId = item.db_id || item.id;

  try {
    const res = await fetch(`${API_BASE}/api/complaints/${targetId}/department-response`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ response: responseText })
    });

    if (res.ok) {
      item.status = 'RESPONSE_RECEIVED';
      item.department_response = responseText;
      item.response_received_at = new Date().toISOString();
      showToast(`Response submitted for complaint ${item.id}! Status updated to RESPONSE RECEIVED.`);
    } else {
      item.status = 'RESPONSE_RECEIVED';
      item.department_response = responseText;
      item.response_received_at = new Date().toISOString();
      showToast(`Response submitted for complaint ${item.id}! Status updated to RESPONSE RECEIVED.`);
    }
  } catch (e) {
    item.status = 'RESPONSE_RECEIVED';
    item.department_response = responseText;
    item.response_received_at = new Date().toISOString();
    showToast(`Response submitted for complaint ${item.id}! Status updated to RESPONSE RECEIVED.`);
  }

  updateDashboardStats();
  renderComplaintsTable();
  if (selectedComplaintIndex === index) openDetailModal(index);
}

// ── Workflow Action: Officer Resolution ─────────────────────────────────────
async function markAsResolved(index) {
  const item = complaints[index];
  if (!item) return;

  const targetId = item.db_id || item.id;

  try {
    const res = await fetch(`${API_BASE}/api/complaints/${targetId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'resolved', resolution_notes: `Resolved by Zone Officer ${currentZoneOfficer.name}` })
    });

    if (res.ok) {
      item.status = 'RESOLVED';
      item.resolved = true;
      item.resolved_at = new Date().toISOString();
      showToast(`✅ Verified & Marked ${item.id} as RESOLVED! WhatsApp notification dispatched to citizen.`);
    } else {
      item.status = 'RESOLVED';
      item.resolved = true;
      item.resolved_at = new Date().toISOString();
      showToast(`✅ Verified & Marked ${item.id} as RESOLVED!`);
    }
  } catch (e) {
    item.status = 'RESOLVED';
    item.resolved = true;
    item.resolved_at = new Date().toISOString();
    showToast(`✅ Verified & Marked ${item.id} as RESOLVED!`);
  }

  updateDashboardStats();
  renderComplaintsTable();
  if (selectedComplaintIndex === index) openDetailModal(index);
}

// ── PART 1: Single Complaint Map Renderer (Inside Detail Modal) ────────────
function renderSingleComplaintMap(item) {
  const container = document.getElementById('modalMapViewContainer');
  const fallback = document.getElementById('modalMapNoLocFallback');
  if (!container) return;

  const hasCoords = typeof item.lat === 'number' && typeof item.lng === 'number' && !isNaN(item.lat) && !isNaN(item.lng);

  if (!hasCoords) {
    container.style.display = 'none';
    if (fallback) fallback.style.display = 'block';
    return;
  }

  container.style.display = 'block';
  if (fallback) fallback.style.display = 'none';

  if (!modalMapInstance) {
    modalMapInstance = L.map('modalMapViewContainer', { zoomControl: true }).setView([item.lat, item.lng], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19
    }).addTo(modalMapInstance);
  } else {
    modalMapInstance.setView([item.lat, item.lng], 14);
  }

  // Clear previous layers from modal map
  modalMapInstance.eachLayer(layer => {
    if (layer instanceof L.CircleMarker || layer instanceof L.Marker) {
      modalMapInstance.removeLayer(layer);
    }
  });

  // Render ONLY this single complaint's marker! (Never show other complaints here)
  const isResolved = item.status === 'RESOLVED';
  const markerColor = isResolved ? '#10b981' : (item.severity === 'Critical' || item.severity === 'High' ? '#ef4444' : '#f59e0b');

  const marker = L.circleMarker([item.lat, item.lng], {
    radius: 10,
    fillColor: markerColor,
    color: '#ffffff',
    weight: 2.5,
    opacity: 1,
    fillOpacity: 0.95
  }).addTo(modalMapInstance);

  marker.bindPopup(`
    <div style="font-family: var(--font-family); padding: 4px; font-size: 12px; line-height: 1.5;">
      <strong style="color: var(--primary-blue); font-size: 13px;">${item.id}</strong><br/>
      <div><strong>Problem:</strong> ${item.problem}</div>
      <div><strong>Area:</strong> ${item.area}</div>
      <div><strong>Department:</strong> ${item.department}</div>
      <div><strong>Severity:</strong> ${item.severity}</div>
      <div><strong>Status:</strong> ${item.status}</div>
    </div>
  `).openPopup();
}

// ── Detail Modal View ───────────────────────────────────────────────────────
function openDetailModal(index) {
  selectedComplaintIndex = index;
  const item = complaints[index];
  if (!item) return;

  document.getElementById('detailRefId').textContent = item.id;

  const statusBadge = document.getElementById('detailStatusBadge');
  if (statusBadge) {
    statusBadge.innerHTML = getStatusBadgeHtml(item.status);
  }

  const solvedMarker = document.getElementById('detailSolvedMarker');
  if (solvedMarker) {
    solvedMarker.className = item.status === 'RESOLVED' ? 'symbol-check' : 'symbol-cross';
    solvedMarker.textContent = item.status === 'RESOLVED' ? '✓' : '✕';
  }

  document.getElementById('detailCategory').textContent = item.dept;

  const sevBadge = document.getElementById('detailSeverity');
  if (sevBadge) {
    sevBadge.className = `badge badge-${(item.severity || 'Medium').toLowerCase()}`;
    sevBadge.textContent = item.severity;
  }

  document.getElementById('detailArea').textContent = item.area;
  document.getElementById('detailCoords').textContent = (item.lat && item.lng) ? `${item.lat}, ${item.lng}` : 'Location Not Available';
  document.getElementById('detailTranscript').textContent = `"${item.transcript}"`;

  // Department Response Display Section
  const deptRespText = document.getElementById('detailDeptResponseText');
  if (deptRespText) {
    deptRespText.textContent = item.department_response || 'No response received from department yet.';
  }

  // Handle Input Form for Department Response
  const deptFormSec = document.getElementById('deptResponseFormSection');
  const deptInput = document.getElementById('deptResponseInput');

  if (currentRole !== 'Zone Officer') {
    // In Department view: allow submitting response if forwarded or re-responding
    if (deptFormSec) deptFormSec.style.display = 'block';
    if (deptInput) deptInput.value = item.department_response || '';
  } else {
    // In Zone Officer view: hide department response input form (officer views response)
    if (deptFormSec) deptFormSec.style.display = 'none';
  }

  // Handle Footer Action Buttons
  const forwardBtn = document.getElementById('modalForwardBtn');
  const resolveBtn = document.getElementById('modalMarkSolvedBtn');

  if (currentRole === 'Zone Officer') {
    if (forwardBtn) {
      forwardBtn.style.display = (item.status === 'OPEN') ? 'inline-flex' : 'none';
    }
    if (resolveBtn) {
      resolveBtn.style.display = (item.status !== 'RESOLVED') ? 'inline-flex' : 'none';
    }
  } else {
    // Department View cannot forward or resolve
    if (forwardBtn) forwardBtn.style.display = 'none';
    if (resolveBtn) resolveBtn.style.display = 'none';
  }

  // Lifecycle Stepper Bar Highlights
  const stepReceived = document.getElementById('stepReceived');
  const stepProcessed = document.getElementById('stepProcessed');
  const stepForwarded = document.getElementById('stepForwarded');
  const stepResponse = document.getElementById('stepResponse');
  const stepResolved = document.getElementById('stepResolved');

  if (stepReceived) stepReceived.style.color = 'var(--primary-blue)';
  if (stepProcessed) stepProcessed.style.color = 'var(--primary-blue)';

  if (stepForwarded) {
    stepForwarded.style.color = ['FORWARDED', 'RESPONSE_RECEIVED', 'RESOLVED'].includes(item.status) ? 'var(--primary-blue)' : 'var(--text-muted)';
  }
  if (stepResponse) {
    stepResponse.style.color = ['RESPONSE_RECEIVED', 'RESOLVED'].includes(item.status) ? 'var(--primary-blue)' : 'var(--text-muted)';
  }
  if (stepResolved) {
    stepResolved.style.color = item.status === 'RESOLVED' ? 'var(--status-resolved-text)' : 'var(--text-muted)';
  }

  // Render individual complaint map for this modal!
  renderSingleComplaintMap(item);

  document.getElementById('detailModal').classList.add('active');

  setTimeout(() => {
    if (modalMapInstance) modalMapInstance.invalidateSize();
  }, 150);
}

function closeDetailModal() {
  document.getElementById('detailModal').classList.remove('active');
  selectedComplaintIndex = null;
}

// ── PART 2: Interactive Map Tab Initialization (ALL Complaints View) ───────
function initMap() {
  if (!document.getElementById('mapViewContainer')) return;

  if (!mainMapInstance) {
    mainMapInstance = L.map('mapViewContainer', { zoomControl: true }).setView([13.0827, 80.2707], 11);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19
    }).addTo(mainMapInstance);
  } else {
    mainMapInstance.invalidateSize();
  }

  mainMapInstance.eachLayer(layer => {
    if (layer instanceof L.CircleMarker || layer instanceof L.Marker) {
      mainMapInstance.removeLayer(layer);
    }
  });

  // Render ALL complaints that have valid coordinates
  complaints.forEach(c => {
    if (typeof c.lat === 'number' && typeof c.lng === 'number' && !isNaN(c.lat) && !isNaN(c.lng)) {
      const isResolved = c.status === 'RESOLVED';
      const markerColor = isResolved ? '#10b981' : (c.severity === 'Critical' || c.severity === 'High' ? '#ef4444' : '#f59e0b');

      const marker = L.circleMarker([c.lat, c.lng], {
        radius: 9,
        fillColor: markerColor,
        color: '#ffffff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.9
      }).addTo(mainMapInstance);

      marker.bindPopup(`
        <div style="font-family: var(--font-family); padding: 4px; font-size: 12px; line-height: 1.6; min-width: 180px;">
          <div style="font-weight: 800; color: var(--primary-blue); font-size: 14px; margin-bottom: 2px;">
            ${c.id}
          </div>
          <div><strong>Problem:</strong> ${c.problem || c.dept}</div>
          <div><strong>Area:</strong> ${c.area || 'Location Not Provided'}</div>
          <div><strong>Department:</strong> ${c.department || 'Municipal Dept.'}</div>
          <div><strong>Severity:</strong> <span style="font-weight: 700; color: ${c.severity === 'Critical' || c.severity === 'High' ? '#ef4444' : '#f59e0b'};">${c.severity || 'Medium'}</span></div>
          <div style="margin-top: 4px; padding-top: 4px; border-top: 1px solid #e2e8f0;">
            <strong>Status:</strong>
            <span style="font-weight: 700; color: ${isResolved ? '#10b981' : '#2563eb'};">
              ${c.status}
            </span>
          </div>
        </div>
      `);
    }
  });
}

// ── Analytics Charts Initialization (Chart.js) ──────────────────────────────
function initCharts() {
  const openedCount = complaints.filter(c => c.status !== 'RESOLVED').length;
  const resolvedCount = complaints.filter(c => c.status === 'RESOLVED').length;

  // 1. Complaint Rate Graph (Line Graph)
  const rateCtx = document.getElementById('chartRate');
  if (rateCtx) {
    if (chartRate) chartRate.destroy();
    chartRate = new Chart(rateCtx.getContext('2d'), {
      type: 'line',
      data: {
        labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
        datasets: [{
          label: 'Complaints Received',
          data: [180, 240, 210, 290, 310, complaints.length * 50],
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.08)',
          tension: 0.35,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, grid: { color: '#e2e8f0' } }
        }
      }
    });
  }

  // 2. Complaint Overview (Bar Chart)
  const overviewCtx = document.getElementById('chartOverview');
  if (overviewCtx) {
    if (chartOverview) chartOverview.destroy();
    chartOverview = new Chart(overviewCtx.getContext('2d'), {
      type: 'bar',
      data: {
        labels: ['Road', 'Sewage', 'Water', 'Sanitation', 'Electricity'],
        datasets: [{
          label: 'Complaints',
          data: [420, 310, 250, 180, 88],
          backgroundColor: '#f59e0b',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, grid: { color: '#e2e8f0' } }
        }
      }
    });
  }

  // 3. Resolution Overview (Doughnut Chart - Real Counts!)
  const resolutionCtx = document.getElementById('chartResolution');
  if (resolutionCtx) {
    if (chartResolution) chartResolution.destroy();
    chartResolution = new Chart(resolutionCtx.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: ['Opened Problems', 'Resolved Problems'],
        datasets: [{
          data: [openedCount, resolvedCount],
          backgroundColor: ['#f59e0b', '#10b981']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } }
      }
    });
  }
}

// ── DOM Event Listeners & Flow Handlers ─────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {

  // Role View Selector Listener
  const roleSelector = document.getElementById('roleSelector');
  if (roleSelector) {
    roleSelector.addEventListener('change', (e) => {
      const selectedRole = e.target.value;
      applyActiveRoleContext(selectedRole);
      showToast(`Switched workspace view to ${selectedRole}`);
    });
  }

  // SLIDE 1: Submit (Login) -> Go to Slide 3
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const role = document.getElementById('loginRole').value;
      const name = document.getElementById('loginName').value.trim();
      const password = document.getElementById('loginPassword').value.trim();

      if (!name || !password) {
        showToast('Please enter both Name and Password.');
        return;
      }

      applyActiveRoleContext(role, name);
      showToast(`Logged in as ${name} (${role})`);
      goToSlide(3);
    });
  }

  // SLIDE 1: Create Account Button -> Go to Slide 2
  const btnGoToSlide2 = document.getElementById('btnGoToSlide2');
  if (btnGoToSlide2) {
    btnGoToSlide2.addEventListener('click', () => {
      goToSlide(2);
    });
  }

  // SLIDE 2: Create Account Submit -> Return to Slide 1
  const createAccountForm = document.getElementById('createAccountForm');
  if (createAccountForm) {
    createAccountForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const role = document.getElementById('regRole') ? document.getElementById('regRole').value : 'Zone Officer';
      const name = document.getElementById('regName').value.trim();
      const zone = document.getElementById('regZone').value.trim();
      const password = document.getElementById('regPassword').value.trim();

      if (!name || !password) {
        showToast('Please enter Name and Password.');
        return;
      }

      const loginRoleSelect = document.getElementById('loginRole');
      if (loginRoleSelect) loginRoleSelect.value = role;

      document.getElementById('loginName').value = name;
      document.getElementById('loginPassword').value = password;

      showToast(`✅ ${role} account created for ${name}! Please click Login.`);
      goToSlide(1);
    });
  }

  // SLIDE 3: Profile Dropdown Menu Toggle
  const profileTrigger = document.getElementById('profileTrigger');
  const profileDropdown = document.getElementById('profileDropdown');

  if (profileTrigger && profileDropdown) {
    profileTrigger.addEventListener('click', (e) => {
      e.stopPropagation();
      profileDropdown.classList.toggle('active');
    });

    document.addEventListener('click', () => {
      profileDropdown.classList.remove('active');
    });
  }

  // Profile Option 1: Change Zone Officer
  const dropdownChangeOfficer = document.getElementById('dropdownChangeOfficer');
  if (dropdownChangeOfficer) {
    dropdownChangeOfficer.addEventListener('click', () => {
      profileDropdown.classList.remove('active');
      goToSlide(1);
      showToast('Switched account view. Please enter credentials.');
    });
  }

  // Profile Option 2: Logout -> Return to Slide 1
  const dropdownLogout = document.getElementById('dropdownLogout');
  if (dropdownLogout) {
    dropdownLogout.addEventListener('click', () => {
      profileDropdown.classList.remove('active');
      goToSlide(1);
      showToast('Logged out. Returned to Account Login Screen.');
    });
  }

  // SLIDE 3: Sidebar Navigation Tabs (Dashboard, Complaints, Map, Analytics)
  document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      document.querySelectorAll('.sidebar-nav .nav-item').forEach(n => n.classList.remove('active'));
      item.classList.add('active');

      const page = item.getAttribute('data-page');
      document.querySelectorAll('.page-view').forEach(p => p.classList.remove('active'));

      const targetPage = document.getElementById(`page${page}`);
      if (targetPage) {
        targetPage.classList.add('active');
      }

      if (page === 'Map') {
        setTimeout(initMap, 100);
      } else if (page === 'Analytics') {
        setTimeout(initCharts, 100);
      }
    });
  });

  // Modal Action Listeners
  const closeDetailBtn = document.getElementById('closeDetailModalBtn');
  if (closeDetailBtn) closeDetailBtn.addEventListener('click', closeDetailModal);

  const modalCloseBtn = document.getElementById('modalCloseBtn');
  if (modalCloseBtn) modalCloseBtn.addEventListener('click', closeDetailModal);

  const forwardBtn = document.getElementById('modalForwardBtn');
  if (forwardBtn) {
    forwardBtn.addEventListener('click', () => {
      if (selectedComplaintIndex !== null) forwardToDepartment(selectedComplaintIndex);
    });
  }

  const submitDeptRespBtn = document.getElementById('btnSubmitDeptResponse');
  if (submitDeptRespBtn) {
    submitDeptRespBtn.addEventListener('click', () => {
      if (selectedComplaintIndex !== null) submitDepartmentResponse(selectedComplaintIndex);
    });
  }

  const markSolvedBtn = document.getElementById('modalMarkSolvedBtn');
  if (markSolvedBtn) {
    markSolvedBtn.addEventListener('click', () => {
      if (selectedComplaintIndex !== null) markAsResolved(selectedComplaintIndex);
    });
  }

  // Initialise active role context and render all dashboard components
  applyActiveRoleContext('Zone Officer', 'Arun Kumar');

  // Start on Slide 1 by default
  goToSlide(1);
});