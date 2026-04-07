// ── SentinelClaw API client ──────────────────────────────────────────
//
// All paths are relative — Vite's dev-server proxy forwards /api and
// /health to the backend at localhost:3001.

import type {
  AgentReport,
  AgentReportDetail,
  AgentTool,
  AgentToolActionResponse,
  AuditEntry,
  AuthorizedTarget,
  ChangePasswordResponse,
  ChatMessage,
  ChatResponse,
  CompareResult,
  CreateScanRequest,
  CreateScanResponse,
  Finding,
  HealthResponse,
  KillResponse,
  LoginResponse,
  MfaActionResponse,
  MfaLoginResponse,
  MfaSetupResponse,
  ScanDetail,
  Scan,
  ScanPhase,
  ScanProfile,
  SystemSetting,
  SystemStatus,
  User,
} from '../types/api';

const BASE = ''; // Vite proxy handles routing to localhost:3001

// ── CSRF-Token aus Cookie lesen ──────────────────────────────────────

function getCsrfToken(): string {
  const match = document.cookie.match(/(?:^|;\s*)sc_csrf=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : '';
}

// ── Generic fetch wrapper ────────────────────────────────────────────

const STATE_CHANGING_METHODS = new Set(['POST', 'PUT', 'DELETE', 'PATCH']);

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const method = (init?.method ?? 'GET').toUpperCase();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init?.headers as Record<string, string>),
  };

  // CSRF-Token bei zustandsändernden Requests als Header mitsenden
  if (STATE_CHANGING_METHODS.has(method)) {
    headers['X-CSRF-Token'] = getCsrfToken();
  }

  // Timeout: 20 Min für Chat (komplexe Scans/OSINT brauchen Zeit), 30s für Rest
  const timeoutMs = url.includes('/chat') ? 1_200_000 : 30_000;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  let res: Response;
  try {
    res = await fetch(`${BASE}${url}`, {
      ...init,
      headers,
      credentials: 'include',
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new Error('Zeitüberschreitung — die Anfrage hat zu lange gedauert. Versuche es erneut.');
    }
    throw err;
  }
  clearTimeout(timeoutId);

  if (res.status === 401 && !url.includes('/auth/login')) {
    // Session abgelaufen — ausloggen
    try {
      const { useAuthStore } = await import('../stores/authStore');
      useAuthStore.getState().logout();
    } catch {
      // Store nicht verfügbar — Seite zeigt Login beim nächsten Render
    }
    throw new Error('Session abgelaufen');
  }

  if (!res.ok) {
    const body = await res.text().catch(() => 'Unknown error');
    throw new Error(`API Error ${res.status}: ${body}`);
  }

  // Handle 204 No Content (DELETE responses, etc.)
  if (res.status === 204) {
    return undefined as T;
  }

  return res.json();
}

// ── Typed API surface ────────────────────────────────────────────────

export const api = {
  /** GET /health */
  health: () => fetchJson<HealthResponse>('/health'),

  /** GET /api/v1/status */
  status: () => fetchJson<SystemStatus>('/api/v1/status'),

  // ── Scans ────────────────────────────────────────────────────────

  scans: {
    /** GET /api/v1/scans — list all scans */
    list: () => fetchJson<Scan[]>('/api/v1/scans'),

    /** GET /api/v1/scans/:id — full scan detail with phases, findings, ports */
    get: (id: string) => fetchJson<ScanDetail>(`/api/v1/scans/${id}`),

    /** POST /api/v1/scans — start a new scan */
    create: (data: CreateScanRequest) =>
      fetchJson<CreateScanResponse>('/api/v1/scans', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    /** DELETE /api/v1/scans/:id */
    delete: (id: string) =>
      fetchJson<void>(`/api/v1/scans/${id}`, { method: 'DELETE' }),

    /** PUT /api/v1/scans/:id/cancel */
    cancel: (id: string) =>
      fetchJson<void>(`/api/v1/scans/${id}/cancel`, { method: 'PUT' }),

    /** GET /api/v1/scans/:id/phases */
    phases: (id: string) =>
      fetchJson<ScanPhase[]>(`/api/v1/scans/${id}/phases`),

    /** GET /api/v1/scans/:id/hosts */
    hosts: (id: string) =>
      fetchJson<unknown[]>(`/api/v1/scans/${id}/hosts`),

    /** GET /api/v1/scans/:id/ports */
    ports: (id: string) =>
      fetchJson<unknown[]>(`/api/v1/scans/${id}/ports`),

    /** GET /api/v1/scans/:id/export?format=... */
    export: (id: string, format?: string) =>
      fetch(
        `${BASE}/api/v1/scans/${id}/export${format ? `?format=${encodeURIComponent(format)}` : ''}`,
        { credentials: 'include' },
      ).then((r) => {
        if (!r.ok) throw new Error(`Export failed: ${r.status}`);
        return r.blob();
      }),

    /** POST /api/v1/scans/compare — compare two scans */
    compare: (data: { scan_id_a: string; scan_id_b: string }) =>
      fetchJson<CompareResult>('/api/v1/scans/compare', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    /** GET /api/v1/scans/:id/report?type=... — returns raw markdown text */
    report: (id: string, type: string) =>
      fetch(
        `${BASE}/api/v1/scans/${id}/report?type=${encodeURIComponent(type)}`,
        { credentials: 'include' },
      ).then((r) => {
        if (!r.ok) throw new Error(`Report failed: ${r.status}`);
        return r.text();
      }),

    /** GET /api/v1/scans/:id/report/pdf?type=... — PDF-Download */
    reportPdf: (id: string, type: string) =>
      fetch(
        `${BASE}/api/v1/scans/${id}/report/pdf?type=${encodeURIComponent(type)}`,
        { credentials: 'include' },
      ).then((r) => {
        if (!r.ok) throw new Error(`PDF-Export failed: ${r.status}`);
        return r.blob();
      }),
  },

  // ── Findings ─────────────────────────────────────────────────────

  findings: {
    /** GET /api/v1/findings — optional nach Severity und/oder Scan-ID filtern */
    list: (severity?: string, scanId?: string) => {
      const params = new URLSearchParams();
      if (severity) params.set('severity', severity);
      if (scanId) params.set('scan_id', scanId);
      const query = params.toString();
      return fetchJson<Finding[]>(`/api/v1/findings${query ? `?${query}` : ''}`);
    },

    /** GET /api/v1/findings/:id */
    get: (id: string) => fetchJson<Finding>(`/api/v1/findings/${id}`),

    /** DELETE /api/v1/findings/:id */
    delete: (id: string) =>
      fetchJson<void>(`/api/v1/findings/${id}`, { method: 'DELETE' }),
  },

  // ── Profiles ─────────────────────────────────────────────────────

  profiles: {
    /** GET /api/v1/profiles — alle Profile (builtin + custom) */
    list: () => fetchJson<ScanProfile[]>('/api/v1/profiles'),

    /** POST /api/v1/profiles — neues Profil erstellen */
    create: (data: Omit<ScanProfile, 'id' | 'is_builtin' | 'created_by' | 'updated_at'>) =>
      fetchJson<ScanProfile>('/api/v1/profiles', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    /** PUT /api/v1/profiles/:id — Profil bearbeiten */
    update: (id: string, data: Omit<ScanProfile, 'id' | 'is_builtin' | 'created_by' | 'updated_at'>) =>
      fetchJson<ScanProfile>(`/api/v1/profiles/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),

    /** DELETE /api/v1/profiles/:id — Custom-Profil löschen */
    delete: (id: string) =>
      fetchJson<void>(`/api/v1/profiles/${id}`, { method: 'DELETE' }),
  },

  // ── Settings ────────────────────────────────────────────────────

  settings: {
    /** GET /api/v1/settings — alle Einstellungen */
    list: () => fetchJson<SystemSetting[]>('/api/v1/settings'),

    /** GET /api/v1/settings/:category — Einstellungen einer Kategorie */
    byCategory: (category: string) =>
      fetchJson<SystemSetting[]>(`/api/v1/settings/${category}`),

    /** PUT /api/v1/settings — Batch-Update */
    update: (settings: Record<string, string>) =>
      fetchJson<{ updated: number }>('/api/v1/settings', {
        method: 'PUT',
        body: JSON.stringify({ settings }),
      }),
  },

  // ── Audit log ────────────────────────────────────────────────────

  /** GET /api/v1/audit?limit=N */
  audit: (limit?: number) =>
    fetchJson<AuditEntry[]>(`/api/v1/audit?limit=${limit ?? 50}`),

  // ── Kill switch ──────────────────────────────────────────────────

  /** POST /api/v1/kill — emergency stop all scans */
  kill: (reason: string) =>
    fetchJson<KillResponse>('/api/v1/kill', {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),

  /** POST /api/v1/kill/reset — Kill-Switch zurücksetzen + Sandbox starten */
  killReset: () =>
    fetchJson<{ status: string; sandbox_started: boolean; message: string }>(
      '/api/v1/kill/reset',
      { method: 'POST' },
    ),

  // ── Chat ──────────────────────────────────────────────────────────

  chat: {
    /** POST /api/v1/chat — send message to agent, get response */
    send: (message: string, scanId?: string) =>
      fetchJson<ChatResponse>('/api/v1/chat', {
        method: 'POST',
        body: JSON.stringify({ message, scan_id: scanId }),
      }),

    /** GET /api/v1/chat/history — get chat messages, optionally filtered by scan_id */
    history: (scanId?: string) =>
      fetchJson<ChatMessage[]>(
        `/api/v1/chat/history${scanId ? `?scan_id=${encodeURIComponent(scanId)}` : ''}`,
      ),

    /** DELETE /api/v1/chat/history — Chat + Agent-Sessions löschen */
    clear: () => fetchJson<void>('/api/v1/chat/history', { method: 'DELETE' }),
  },

  // ── Agent Reports ────────────────────────────────────────────────

  agentReports: {
    /** GET /api/v1/chat/reports/agent — alle Agent-Reports */
    list: () =>
      fetchJson<AgentReport[]>('/api/v1/chat/reports/agent'),

    /** GET /api/v1/chat/reports/agent/:id — einzelner Report mit Inhalt */
    get: (id: string) =>
      fetchJson<AgentReportDetail>(`/api/v1/chat/reports/agent/${id}`),

    /** DELETE /api/v1/chat/reports/agent/:id — Report löschen */
    delete: (id: string) =>
      fetchJson<{ status: string }>(`/api/v1/chat/reports/agent/${id}`, {
        method: 'DELETE',
      }),
  },

  // ── Agent Tools ──────────────────────────────────────────────────

  agentTools: {
    /** GET /api/v1/agent/tools — alle Tools mit Status */
    list: () => fetchJson<AgentTool[]>('/api/v1/agent/tools'),

    /** POST /api/v1/agent/tools/:name/install */
    install: (name: string) =>
      fetchJson<AgentToolActionResponse>(`/api/v1/agent/tools/${name}/install`, {
        method: 'POST',
      }),

    /** DELETE /api/v1/agent/tools/:name */
    uninstall: (name: string) =>
      fetchJson<AgentToolActionResponse>(`/api/v1/agent/tools/${name}`, {
        method: 'DELETE',
      }),
  },

  // ── Approvals (Eskalationsgenehmigungen) ──────────────────────────

  approvals: {
    /** GET /api/v1/approvals — alle Approval-Requests */
    list: (status?: string) =>
      fetchJson<Record<string, unknown>[]>(
        `/api/v1/approvals${status ? `?status=${encodeURIComponent(status)}` : ''}`,
      ),

    /** PUT /api/v1/approvals/:id/approve */
    approve: (id: string, reason?: string) =>
      fetchJson<{ status: string }>(`/api/v1/approvals/${id}/approve`, {
        method: 'PUT',
        body: JSON.stringify({ reason: reason ?? '' }),
      }),

    /** PUT /api/v1/approvals/:id/reject */
    reject: (id: string, reason?: string) =>
      fetchJson<{ status: string }>(`/api/v1/approvals/${id}/reject`, {
        method: 'PUT',
        body: JSON.stringify({ reason: reason ?? '' }),
      }),
  },

  // ── Kill-Verifikation ────────────────────────────────────────────

  killStatus: () => fetchJson<Record<string, unknown>>('/api/v1/kill/status'),

  // ── Workspace (NemoClaw Agent-Konfiguration) ─────────────────────

  workspace: {
    /** GET /api/v1/workspace — alle Workspace-Dateien */
    list: () =>
      fetchJson<{ name: string; content: string; size: number; modified_at: string }[]>(
        '/api/v1/workspace',
      ),

    /** GET /api/v1/workspace/:name — einzelne Datei */
    get: (name: string) =>
      fetchJson<{ name: string; content: string; size: number; modified_at: string }>(
        `/api/v1/workspace/${encodeURIComponent(name)}`,
      ),

    /** PUT /api/v1/workspace/:name — Datei aktualisieren */
    update: (name: string, content: string) =>
      fetchJson<{ name: string; content: string; updated_at: string }>(
        `/api/v1/workspace/${encodeURIComponent(name)}`,
        {
          method: 'PUT',
          body: JSON.stringify({ content }),
        },
      ),
  },

  // ── Whitelist (Autorisierte Ziele) ────────────────────────────────

  whitelist: {
    /** GET /api/v1/whitelist — alle autorisierten Ziele */
    list: () => fetchJson<AuthorizedTarget[]>('/api/v1/whitelist'),

    /** POST /api/v1/whitelist — Ziel autorisieren */
    authorize: (target: string, confirmation: string, notes?: string) =>
      fetchJson<AuthorizedTarget>('/api/v1/whitelist', {
        method: 'POST',
        body: JSON.stringify({ target, confirmation, notes: notes ?? '' }),
      }),

    /** DELETE /api/v1/whitelist/:id — Autorisierung widerrufen */
    revoke: (id: string) =>
      fetchJson<void>(`/api/v1/whitelist/${id}`, { method: 'DELETE' }),

    /** GET /api/v1/whitelist/policy — Policy-Status */
    policy: () => fetchJson<Record<string, string>>('/api/v1/whitelist/policy'),
  },

  // ── Auth ──────────────────────────────────────────────────────────

  auth: {
    /** POST /api/v1/auth/login — authenticate and receive JWT + user */
    login: (email: string, password: string) =>
      fetchJson<LoginResponse>('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),

    /** POST /api/v1/auth/logout — serverseitiges Logout (Cookie wird gelöscht) */
    logout: () =>
      fetchJson<{ status: string }>('/api/v1/auth/logout', {
        method: 'POST',
      }),

    /** GET /api/v1/auth/me — current authenticated user */
    me: () => fetchJson<User>('/api/v1/auth/me'),

    /** GET /api/v1/auth/users — list all users (admin only) */
    users: () => fetchJson<User[]>('/api/v1/auth/users'),

    /** POST /api/v1/auth/mfa/login — MFA-Code nach Passwort-Login prüfen */
    mfaLogin: (mfaSession: string, token: string) =>
      fetchJson<MfaLoginResponse>('/api/v1/auth/mfa/login', {
        method: 'POST',
        body: JSON.stringify({ mfa_session: mfaSession, token }),
      }),

    /** POST /api/v1/auth/mfa/setup — MFA für eigenen Account einrichten */
    mfaSetup: () =>
      fetchJson<MfaSetupResponse>('/api/v1/auth/mfa/setup', { method: 'POST' }),

    /** POST /api/v1/auth/mfa/verify — Ersten TOTP-Code bestätigen */
    mfaVerify: (secret: string, token: string) =>
      fetchJson<MfaActionResponse>('/api/v1/auth/mfa/verify', {
        method: 'POST',
        body: JSON.stringify({ secret, token }),
      }),

    /** POST /api/v1/auth/mfa/disable — MFA deaktivieren */
    mfaDisable: (token: string) =>
      fetchJson<MfaActionResponse>('/api/v1/auth/mfa/disable', {
        method: 'POST',
        body: JSON.stringify({ token }),
      }),

    /** POST /api/v1/auth/change-password — Eigenes Passwort ändern */
    changePassword: (oldPassword: string, newPassword: string) =>
      fetchJson<ChangePasswordResponse>('/api/v1/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
      }),
  },
};
