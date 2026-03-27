/**
 * Typed API client for the Rowboat FastAPI backend.
 * Uses the Next.js rewrite proxy (/api/* → FastAPI) so no CORS issues in dev.
 */

const API_BASE = "/api";

function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("auth_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `API error ${res.status}`);
  }
  return res.json();
}

// ── Auth ──────────────────────────────────────────────────────────────

export interface User {
  id: string;
  name: string;
  email: string;
  username?: string;
  preferences?: Record<string, unknown>;
  profile?: { display_name?: string; bio?: string; avatar_url?: string; interest_tags?: string[] };
  availability?: { timezone?: string; weekly_windows?: { day: string; start: string; end: string }[]; notes?: string };
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export const auth = {
  register: (name: string, email: string, password: string, username?: string) =>
    request<LoginResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password, username }),
    }),

  login: (email: string, password: string) => {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    return fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      body: form,
    }).then(async (res) => {
      if (!res.ok) throw new Error((await res.json()).detail || "Login failed");
      return res.json() as Promise<LoginResponse>;
    });
  },

  me: () => request<User>("/auth/me"),

  googleUrl: () => request<{ auth_url: string }>("/auth/google/url"),
};

// ── Profile ───────────────────────────────────────────────────────────

export const profile = {
  get: () => request<User["profile"]>("/profile/me"),
  update: (data: User["profile"]) =>
    request<User["profile"]>("/profile/me", { method: "PUT", body: JSON.stringify(data) }),
  getAvailability: () => request<User["availability"]>("/profile/me/availability"),
  updateAvailability: (data: User["availability"]) =>
    request<User["availability"]>("/profile/me/availability", { method: "PUT", body: JSON.stringify(data) }),
};

// ── Friends ───────────────────────────────────────────────────────────

export const friends = {
  list: (userId: string) => request<User[]>(`/friends/${userId}/friends`),
  incoming: (userId: string) => request<unknown[]>(`/friends/${userId}/requests/incoming`),
  outgoing: (userId: string) => request<unknown[]>(`/friends/${userId}/requests/outgoing`),
  sendRequest: (userId: string, to: { to_email?: string; to_username?: string }) =>
    request<unknown>(`/friends/${userId}/request`, { method: "POST", body: JSON.stringify(to) }),
  respond: (userId: string, friendshipId: number, accept: boolean) =>
    request<unknown>(`/friends/${userId}/respond/${friendshipId}`, {
      method: "POST",
      body: JSON.stringify({ accept }),
    }),
  remove: (userId: string, friendId: string) =>
    request<unknown>(`/friends/${userId}/friends/${friendId}`, { method: "DELETE" }),
};

// ── Hangouts ──────────────────────────────────────────────────────────

export interface Hangout {
  id: string;
  title: string;
  description?: string;
  time_window?: { start?: string; end?: string };
  location_area?: string;
  tags: string[];
  source: string;
  created_by?: string;
}

export interface SuggestedMatch {
  id: string;
  hangout_id: string;
  member_user_ids: string[];
  score: number;
  status: string;
  group_id?: string;
}

export const hangouts = {
  list: () => request<Hangout[]>("/hangouts"),
  feed: () => request<Hangout[]>("/hangouts/feed/me"),
  create: (data: { title: string; description?: string; tags?: string[]; location_area?: string }) =>
    request<Hangout>("/hangouts", { method: "POST", body: JSON.stringify(data) }),
  swipe: (hangoutId: string, action: "pass" | "interested") =>
    request<{ user_id: string; hangout_id: string; action: string }>(
      `/hangouts/${hangoutId}/swipe`,
      { method: "POST", body: JSON.stringify({ action }) },
    ),
  generateMatches: (hangoutId: string) =>
    request<SuggestedMatch[]>(`/hangouts/${hangoutId}/generate-matches`, { method: "POST" }),
  createGroupFromMatch: (matchId: string) =>
    request<SuggestedMatch>(`/hangouts/matches/${matchId}/create-group`, { method: "POST" }),
};
