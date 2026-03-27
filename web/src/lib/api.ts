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

// ── Config status ─────────────────────────────────────────────────────

export interface ConfigStatus {
  gemini: boolean;
  anthropic: boolean;
  ai_ready: boolean;
  yelp: boolean;
  eventbrite: boolean;
  ticketmaster: boolean;
  google_places: boolean;
  google_calendar: boolean;
}

export const configStatus = () =>
  request<ConfigStatus>("/config/status");

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

// ── Groups ────────────────────────────────────────────────────────────

export interface Group {
  id: string;
  name: string;
  member_ids: string[];
  created_by: string;
}

export const groups = {
  create: (name: string, creator_name: string, creator_email: string) =>
    request<Group>("/groups/", {
      method: "POST",
      body: JSON.stringify({ name, creator_name, creator_email }),
    }),
  get: (groupId: string) => request<Group>(`/groups/${groupId}`),
  addMember: (groupId: string, name: string, email: string) =>
    request<Group>(`/groups/${groupId}/members`, {
      method: "POST",
      body: JSON.stringify({ name, email }),
    }),
  getMembers: (groupId: string) => request<User[]>(`/groups/${groupId}/members`),
};

// ── Preferences ───────────────────────────────────────────────────────

export interface UserPreferences {
  cuisine_preferences: string[];
  activity_preferences: string[];
  dietary_restrictions: string[];
  budget_max: "$" | "$$" | "$$$" | "$$$$";
  dealbreakers: string[];
  preferred_neighborhoods: string[];
  group_size_comfort: [number, number];
  accessibility_needs: string[];
}

export const preferences = {
  get: (userId: string) => request<UserPreferences>(`/preferences/${userId}`),
  save: (userId: string, prefs: Partial<UserPreferences>) =>
    request<UserPreferences>(`/preferences/${userId}`, {
      method: "POST",
      body: JSON.stringify(prefs),
    }),
};

// ── Venue types ────────────────────────────────────────────────────────

export interface Venue {
  id: string;
  name: string;
  category: string;
  address: string;
  categories: string[];
  rating?: number;
  review_count?: number;
  price_tier?: string;
  url?: string;
  image_url?: string;
  source?: string;
}

export interface ScoredVenue extends Venue {
  score: number;
  passed_hard_constraints: boolean;
  explanation?: string;
  violation_reasons?: string[];
}

export interface SearchResult {
  venues: Venue[];
  summary: string;
  sources_searched: string[];
}

export interface RecommendationResult {
  ranked_venues: ScoredVenue[];
  rejected_venues: ScoredVenue[];
  summary: string;
  constraint_summary: string;
}

export interface OrchestratorPlan {
  group_name: string;
  members: string[];
  request_summary: string;
  venues_found: number;
  ranked_venues: ScoredVenue[];
  rejected_venues: ScoredVenue[];
  available_slots: Record<string, unknown>[];
  recommended_venue: Record<string, unknown> | null;
  recommended_slot: Record<string, unknown> | null;
  estimated_cost_per_person: string;
  itinerary_summary: string;
  rag_insights: string;
  steps_completed: string[];
  agent_log: string[];
}

// ── Plans (AI agents) ─────────────────────────────────────────────────

export const plans = {
  search: (query: string, location = "Pittsburgh, PA", max_results = 10) =>
    request<SearchResult>("/plans/search", {
      method: "POST",
      body: JSON.stringify({ query, location, max_results }),
    }),

  recommend: (
    venues: Venue[],
    preferences_list: Partial<UserPreferences>[],
    groupId: string,
    budgetMax = "$$",
    dietaryRestrictions: string[] = [],
    dealbreakers: string[] = [],
    memberNames: string[] = [],
  ) =>
    request<RecommendationResult>("/plans/recommend", {
      method: "POST",
      body: JSON.stringify({
        venues,
        preferences: preferences_list,
        group_id: groupId,
        budget_max: budgetMax,
        dietary_restrictions: dietaryRestrictions,
        dealbreakers,
        member_names: memberNames,
      }),
    }),

  orchestrate: (payload: {
    request: string;
    group_name?: string;
    members?: { name: string; email: string }[];
    preferences?: Partial<UserPreferences>[];
    location?: string;
    date_range_start?: string;
    date_range_end?: string;
    earliest_time?: string;
    latest_time?: string;
  }) =>
    request<OrchestratorPlan>("/plans/orchestrate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

// ── Calendar ──────────────────────────────────────────────────────────

export const calendar = {
  status: (userId: string) =>
    request<{ connected: boolean }>(`/calendar/status/${userId}`),
  authUrl: () => request<{ auth_url: string }>("/calendar/auth-url"),
  book: (payload: {
    organizer_user_id: string;
    group_id: string;
    venue_name: string;
    venue_address: string;
    start_time: string;
    end_time: string;
    attendee_emails: string[];
  }) =>
    request<{ message: string; calendar_link?: string }>("/calendar/book", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
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
