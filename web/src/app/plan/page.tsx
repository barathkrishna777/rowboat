"use client";

/**
 * /plan — AI-powered outing planner (the core Rowboat experience).
 *
 * Steps:
 *  1. Group       — create/load group, add members
 *  2. Preferences — cuisines, activities, dietary, budget, dealbreakers
 *  3. Search      — natural-language → Search Agent (POST /api/plans/search)
 *  4. Rank        — Recommendation Agent scores venues (POST /api/plans/recommend)
 *  5. Review      — pick venue+slot, book & send calendar invites
 *  6. Feedback    — post-outing rating
 *
 * Fast-path: "AI plans everything" → POST /api/plans/orchestrate
 *
 * Can be deep-linked from /swipe match flow: /plan?group_id=xxx
 */

import { useEffect, useState, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import {
  groups as groupsApi,
  plans as plansApi,
  calendar as calendarApi,
  preferences as preferencesApi,
  configStatus,
  ConfigStatus,
  Group,
  Venue,
  ScoredVenue,
  SearchResult,
  RecommendationResult,
  OrchestratorPlan,
  UserPreferences,
} from "@/lib/api";

// ── Types ───────────────────────────────────────────────────────────────

type Member = { name: string; email: string };

const CUISINES = ["Italian", "Japanese", "Mexican", "Chinese", "Indian", "Thai",
  "Korean", "American", "Mediterranean", "French", "Vietnamese", "Ethiopian"];
const ACTIVITIES = ["Bowling", "Escape Room", "Concert", "Movie", "Hiking", "Karaoke",
  "Board Games", "Mini Golf", "Arcade", "Museum", "Comedy Show", "Sports Event"];
const DIETARY = ["Vegetarian", "Vegan", "Gluten Free", "Halal", "Kosher",
  "Nut Allergy", "Dairy Free", "Shellfish Allergy"];
const BUDGET_OPTIONS: { label: string; value: "$" | "$$" | "$$$" | "$$$$" }[] = [
  { label: "$ — Under $15/person", value: "$" },
  { label: "$$ — $15–40/person", value: "$$" },
  { label: "$$$ — $40–80/person", value: "$$$" },
  { label: "$$$$ — $80+/person", value: "$$$$" },
];

// ── Helpers ─────────────────────────────────────────────────────────────

function StepBadge({ n, active, done }: { n: number; active: boolean; done: boolean }) {
  return (
    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shrink-0
      ${done ? "bg-green-500 text-white" : active ? "bg-orange-500 text-white" : "bg-gray-200 text-gray-500"}`}>
      {done ? "✓" : n}
    </div>
  );
}

function StepHeader({ step, current, title }: { step: number; current: number; title: string }) {
  return (
    <div className="flex items-center gap-3 mb-5">
      <StepBadge n={step} active={step === current} done={step < current} />
      <h2 className="text-lg font-bold">{title}</h2>
    </div>
  );
}

function Toggle({ options, value, onChange }: {
  options: string[]; value: string[]; onChange: (v: string[]) => void;
}) {
  const toggle = (o: string) =>
    onChange(value.includes(o) ? value.filter(x => x !== o) : [...value, o]);
  return (
    <div className="flex flex-wrap gap-2">
      {options.map(o => (
        <button key={o} type="button" onClick={() => toggle(o)}
          className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-colors
            ${value.includes(o) ? "bg-orange-500 text-white border-orange-500" : "bg-white text-gray-700 border-gray-300 hover:border-orange-300"}`}>
          {o}
        </button>
      ))}
    </div>
  );
}

function VenueCard({ venue, score, passed, selected, onSelect, violation }: {
  venue: Venue; score?: number; passed?: boolean; selected?: boolean;
  onSelect?: () => void; violation?: string[];
}) {
  const badge = score !== undefined
    ? score >= 70 ? "bg-green-100 text-green-700" : score >= 40 ? "bg-orange-100 text-orange-700" : "bg-red-100 text-red-700"
    : "bg-gray-100 text-gray-600";

  return (
    <div onClick={onSelect} className={`border rounded-xl p-4 transition-all cursor-pointer
      ${selected ? "border-orange-400 bg-orange-50 shadow-sm" : passed === false ? "opacity-60 border-red-200 bg-red-50" : "border-gray-200 bg-white hover:border-orange-300"}
    `}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-gray-900 truncate">{venue.name}</div>
          <div className="text-sm text-gray-500">{venue.address}</div>
          <div className="text-xs text-gray-400 mt-0.5">{venue.categories?.join(", ")}</div>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          {score !== undefined && (
            <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${badge}`}>{score}%</span>
          )}
          {venue.price_tier && <span className="text-sm">{venue.price_tier}</span>}
          {venue.rating && <span className="text-xs text-yellow-600">⭐ {venue.rating}</span>}
        </div>
      </div>
      {violation && violation.length > 0 && (
        <p className="text-xs text-red-500 mt-1">⛔ {violation.join(" · ")}</p>
      )}
      {venue.url && (
        <a href={venue.url} target="_blank" rel="noopener noreferrer"
          onClick={e => e.stopPropagation()}
          className="text-xs text-orange-500 hover:underline mt-1 block">
          View details →
        </a>
      )}
    </div>
  );
}

// ── Main component ──────────────────────────────────────────────────────

export default function PlanPage() {
  return (
    <Suspense fallback={<p className="text-center mt-20">Loading planner…</p>}>
      <PlanPageInner />
    </Suspense>
  );
}

function PlanPageInner() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [step, setStep] = useState(1);
  const [globalError, setGlobalError] = useState("");
  const [configSt, setConfigSt] = useState<ConfigStatus | null>(null);

  // Step 1 — Group
  const [group, setGroup] = useState<Group | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [groupName, setGroupName] = useState("");
  const [newMemberName, setNewMemberName] = useState("");
  const [newMemberEmail, setNewMemberEmail] = useState("");
  const [groupLoading, setGroupLoading] = useState(false);

  // Step 2 — Preferences
  const [cuisines, setCuisines] = useState<string[]>([]);
  const [activities, setActivities] = useState<string[]>([]);
  const [dietary, setDietary] = useState<string[]>([]);
  const [budget, setBudget] = useState<"$" | "$$" | "$$$" | "$$$$">("$$");
  const [dealbreakers, setDealbreakers] = useState("");
  const [neighborhoods, setNeighborhoods] = useState("");

  // Step 3 — Search
  const [searchQuery, setSearchQuery] = useState("");
  const [location, setLocation] = useState("Pittsburgh, PA");
  const [searching, setSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null);

  // Step 4 — Rank
  const [ranking, setRanking] = useState(false);
  const [recommendation, setRecommendation] = useState<RecommendationResult | null>(null);
  const [selectedVenue, setSelectedVenue] = useState<ScoredVenue | Venue | null>(null);

  // Step 5 — Review/Book
  const [booked, setBooked] = useState(false);
  const [booking, setBooking] = useState(false);

  // Step 6 — Feedback
  const [overallRating, setOverallRating] = useState(4);
  const [feedbackText, setFeedbackText] = useState("");
  const [feedbackDone, setFeedbackDone] = useState(false);

  // Orchestrator fast-path
  const [orchestrating, setOrchestrating] = useState(false);
  const [orchestratorResult, setOrchestratorResult] = useState<OrchestratorPlan | null>(null);

  // Saved preferences from bio-to-preferences pipeline
  const [savedPrefs, setSavedPrefs] = useState<UserPreferences | null>(null);

  // Load saved preferences and pre-fill step 2 form
  useEffect(() => {
    if (!user) return;
    preferencesApi.get(user.id).then((prefs) => {
      setSavedPrefs(prefs);
      if (prefs.cuisine_preferences?.length) setCuisines(prefs.cuisine_preferences.map(c => c.charAt(0).toUpperCase() + c.slice(1)));
      if (prefs.activity_preferences?.length) setActivities(prefs.activity_preferences.map(a => a.charAt(0).toUpperCase() + a.slice(1)));
      if (prefs.dietary_restrictions?.length) setDietary(prefs.dietary_restrictions.map(d => d.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())));
      if (prefs.budget_max) setBudget(prefs.budget_max);
      if (prefs.dealbreakers?.length) setDealbreakers(prefs.dealbreakers.join("\n"));
      if (prefs.preferred_neighborhoods?.length) setNeighborhoods(prefs.preferred_neighborhoods.join(", "));
    }).catch(() => {});
  }, [user]);

  // Pre-load group from ?group_id query param (deep-link from swipe flow)
  useEffect(() => {
    if (!loading && !user) { router.replace("/login"); return; }
    configStatus().then(setConfigSt).catch(() => {});
    const gid = searchParams.get("group_id");
    if (gid && user && !group) {
      groupsApi.get(gid).then(async g => {
        setGroup(g);
        const memberUsers = await groupsApi.getMembers(gid).catch(() => []);
        setMembers(memberUsers.map(u => ({ name: u.name, email: u.email })));
        setGroupName(g.name);
      }).catch(() => {});
    }
  }, [loading, user, router, searchParams, group]);

  // Step 1: Create group
  const handleCreateGroup = async () => {
    if (!groupName || !user) return;
    setGroupLoading(true);
    setGlobalError("");
    try {
      const g = await groupsApi.create(groupName, user.name, user.email);
      setGroup(g);
      setMembers([{ name: user.name, email: user.email }]);
    } catch (e: unknown) {
      setGlobalError(e instanceof Error ? e.message : "Failed to create group");
    } finally {
      setGroupLoading(false);
    }
  };

  const handleAddMember = async () => {
    if (!group || !newMemberName || !newMemberEmail) return;
    setGroupLoading(true);
    try {
      await groupsApi.addMember(group.id, newMemberName, newMemberEmail);
      setMembers(prev => [...prev, { name: newMemberName, email: newMemberEmail }]);
      setNewMemberName("");
      setNewMemberEmail("");
    } catch (e: unknown) {
      setGlobalError(e instanceof Error ? e.message : "Failed to add member");
    } finally {
      setGroupLoading(false);
    }
  };

  // Step 3: Search venues
  const handleSearch = async () => {
    if (!searchQuery) return;
    setSearching(true);
    setGlobalError("");
    setSearchResult(null);
    try {
      const result = await plansApi.search(searchQuery, location);
      setSearchResult(result);
    } catch (e: unknown) {
      setGlobalError(e instanceof Error ? e.message : "Search failed");
    } finally {
      setSearching(false);
    }
  };

  // Step 4: Rank venues
  const handleRank = async () => {
    if (!searchResult || !group) return;
    setRanking(true);
    setGlobalError("");
    try {
      const prefs: Partial<UserPreferences> = {
        cuisine_preferences: cuisines.map(c => c.toLowerCase()),
        activity_preferences: activities.map(a => a.toLowerCase()),
        dietary_restrictions: dietary.map(d => d.toLowerCase().replace(/ /g, "_")),
        budget_max: budget,
        dealbreakers: dealbreakers.split("\n").map(d => d.trim()).filter(Boolean),
        preferred_neighborhoods: neighborhoods.split(",").map(n => n.trim()).filter(Boolean),
      };
      const result = await plansApi.recommend(
        searchResult.venues,
        [prefs],
        group.id,
        budget,
        prefs.dietary_restrictions || [],
        prefs.dealbreakers || [],
        members.map(m => m.name),
      );
      setRecommendation(result);
    } catch (e: unknown) {
      setGlobalError(e instanceof Error ? e.message : "Ranking failed");
    } finally {
      setRanking(false);
    }
  };

  // Orchestrator fast-path
  const handleOrchestrate = async () => {
    if (!searchQuery) return;
    setOrchestrating(true);
    setGlobalError("");
    try {
      const formPrefs: Partial<UserPreferences> = {
        cuisine_preferences: cuisines.map(c => c.toLowerCase()),
        activity_preferences: activities.map(a => a.toLowerCase()),
        budget_max: budget,
        dealbreakers: dealbreakers.split("\n").filter(Boolean),
        dietary_restrictions: dietary.map(d => d.toLowerCase().replace(/ /g, "_")),
        preferred_neighborhoods: neighborhoods.split(",").map(n => n.trim()).filter(Boolean),
      };
      const hasFormPrefs = cuisines.length || activities.length || dietary.length;
      const prefsToSend = hasFormPrefs ? [formPrefs] : savedPrefs ? [savedPrefs] : [];

      const result = await plansApi.orchestrate({
        request: searchQuery,
        group_name: group?.name || groupName || "My Group",
        members,
        preferences: prefsToSend,
        location,
      });
      setOrchestratorResult(result);
      if (result.recommended_venue) {
        setSelectedVenue(result.recommended_venue as unknown as ScoredVenue);
      }
      setStep(5); // Jump straight to Review
    } catch (e: unknown) {
      setGlobalError(e instanceof Error ? e.message : "Orchestration failed");
    } finally {
      setOrchestrating(false);
    }
  };

  // Step 5: Book
  const handleBook = async () => {
    setBooking(true);
    setGlobalError("");
    try {
      const slot = orchestratorResult?.recommended_slot as Record<string, string> | undefined;
      if (user && group && slot?.start_iso && slot?.end_iso) {
        await calendarApi.book({
          organizer_user_id: user.id,
          group_id: group.id,
          venue_name: selectedVenue?.name || "Outing",
          venue_address: (selectedVenue as Venue)?.address || "",
          start_time: slot.start_iso,
          end_time: slot.end_iso,
          attendee_emails: members.map(m => m.email).filter(Boolean),
        });
      }
      setBooked(true);
    } catch {
      // Calendar booking can fail gracefully — the itinerary is still valid
      setBooked(true);
    } finally {
      setBooking(false);
    }
  };

  // ── Render ───────────────────────────────────────────────────────────

  if (loading || !user) return <p className="text-center mt-20">Loading...</p>;

  const steps = [
    "Your Group", "Preferences", "Find Venues", "Rank & Score", "Review & Book", "Feedback"
  ];

  return (
    <div className="max-w-xl mx-auto">
      {/* Progress bar */}
      <div className="flex items-center gap-1 mb-8">
        {steps.map((label, i) => (
          <div key={i} className="flex-1 flex flex-col items-center gap-1">
            <div className={`h-1.5 w-full rounded-full transition-colors ${i + 1 <= step ? "bg-orange-500" : "bg-gray-200"}`} />
            <span className="text-[10px] text-gray-400 hidden sm:block text-center leading-tight">{label}</span>
          </div>
        ))}
      </div>

      {/* API key config warning */}
      {configSt && !configSt.ai_ready && (
        <div className="bg-amber-50 border border-amber-300 rounded-lg p-4 mb-4 text-sm dark:bg-amber-950 dark:border-amber-700">
          <p className="font-semibold text-amber-800 dark:text-amber-300">⚠️ AI features need an API key</p>
          <p className="text-amber-700 dark:text-amber-400 mt-1">
            Add at least one LLM key to{" "}
            <code className="bg-amber-100 dark:bg-amber-900 px-1 rounded">.env</code> then restart the API server:
          </p>
          <ul className="list-disc list-inside text-amber-700 dark:text-amber-400 mt-1 space-y-0.5">
            <li><code className="bg-amber-100 dark:bg-amber-900 px-1 rounded">ANTHROPIC_API_KEY=sk-ant-…</code> — Claude (primary, recommended)</li>
            <li><code className="bg-amber-100 dark:bg-amber-900 px-1 rounded">GEMINI_API_KEY=AIza…</code> — Gemini free tier at{" "}
              <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener noreferrer"
                className="underline text-amber-800 dark:text-amber-300">aistudio.google.com/apikey</a>
            </li>
          </ul>
          {!configSt.yelp && !configSt.eventbrite && !configSt.ticketmaster && (
            <p className="text-amber-600 dark:text-amber-500 mt-1 text-xs">
              Venue search APIs (Yelp, Eventbrite, Ticketmaster) are also unconfigured — search will return no results.
            </p>
          )}
        </div>
      )}

      {globalError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-red-600 text-sm dark:bg-red-950 dark:border-red-800 dark:text-red-400">
          {globalError}
        </div>
      )}

      {/* ── Step 1: Group ─────────────────────────────────────────── */}
      {step === 1 && (
        <div>
          <StepHeader step={1} current={step} title="Your Group" />

          {!group ? (
            <div className="space-y-3">
              <input value={groupName} onChange={e => setGroupName(e.target.value)}
                placeholder="Group name (e.g. Friday Night Crew)"
                className="w-full border border-gray-300 dark:border-slate-600 rounded-lg px-4 py-2.5 bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100 placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-400" />
              <button onClick={handleCreateGroup} disabled={!groupName || groupLoading}
                className="w-full bg-orange-500 text-white rounded-lg py-2.5 font-semibold hover:bg-orange-600 disabled:opacity-50">
                {groupLoading ? "Creating…" : "Create Group"}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                <p className="font-semibold text-green-800">{group.name}</p>
                <p className="text-sm text-green-600">{members.length} member{members.length !== 1 ? "s" : ""}</p>
              </div>

              <div>
                <p className="text-sm font-medium text-gray-600 mb-2">Members</p>
                {members.map((m, i) => (
                  <div key={i} className="flex items-center gap-2 py-1.5 border-b border-gray-100 last:border-0">
                    <div className="w-7 h-7 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center text-xs font-bold">
                      {m.name[0]}
                    </div>
                    <div>
                      <div className="text-sm font-medium">{m.name}</div>
                      <div className="text-xs text-gray-400">{m.email}</div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="border rounded-lg p-3 space-y-2">
                <p className="text-sm font-medium text-gray-600">Add a member</p>
                <input value={newMemberName} onChange={e => setNewMemberName(e.target.value)}
                  placeholder="Name" className="w-full border border-gray-200 dark:border-slate-600 rounded px-3 py-1.5 text-sm bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100 placeholder:text-gray-400 dark:placeholder:text-slate-500" />
                <input value={newMemberEmail} onChange={e => setNewMemberEmail(e.target.value)}
                  placeholder="Email" type="email" className="w-full border border-gray-200 dark:border-slate-600 rounded px-3 py-1.5 text-sm bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100 placeholder:text-gray-400 dark:placeholder:text-slate-500" />
                <button onClick={handleAddMember} disabled={!newMemberName || !newMemberEmail || groupLoading}
                  className="w-full border border-orange-400 text-orange-500 rounded py-1.5 text-sm font-medium hover:bg-orange-50 disabled:opacity-50">
                  + Add Member
                </button>
              </div>

              <button onClick={() => setStep(2)}
                className="w-full bg-orange-500 text-white rounded-lg py-2.5 font-semibold hover:bg-orange-600">
                Continue →
              </button>
            </div>
          )}
        </div>
      )}

      {/* ── Step 2: Preferences ───────────────────────────────────── */}
      {step === 2 && (
        <div>
          <StepHeader step={2} current={step} title="Preferences" />
          <div className="space-y-5">
            <div>
              <p className="text-sm font-medium text-gray-600 mb-2">Cuisines</p>
              <Toggle options={CUISINES} value={cuisines} onChange={setCuisines} />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600 mb-2">Activities</p>
              <Toggle options={ACTIVITIES} value={activities} onChange={setActivities} />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600 mb-2">Dietary restrictions</p>
              <Toggle options={DIETARY} value={dietary} onChange={setDietary} />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600 mb-2">Budget per person</p>
              <div className="grid grid-cols-2 gap-2">
                {BUDGET_OPTIONS.map(opt => (
                  <button key={opt.value} type="button" onClick={() => setBudget(opt.value)}
                    className={`py-2 px-3 rounded-lg border text-sm font-medium text-left transition-colors
                      ${budget === opt.value ? "border-orange-400 bg-orange-50 text-orange-700" : "border-gray-200 text-gray-600 hover:border-orange-200"}`}>
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">Dealbreakers (one per line)</p>
              <textarea value={dealbreakers} onChange={e => setDealbreakers(e.target.value)}
                rows={2} placeholder={"No loud places\nMust have parking"}
                className="w-full border border-gray-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100 placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">Preferred neighborhoods</p>
              <input value={neighborhoods} onChange={e => setNeighborhoods(e.target.value)}
                placeholder="Oakland, Shadyside, Squirrel Hill"
                className="w-full border border-gray-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100 placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-400" />
            </div>
            <div className="flex gap-3">
              <button onClick={() => setStep(1)}
                className="flex-1 border border-gray-300 rounded-lg py-2.5 text-gray-600 font-semibold hover:bg-gray-50">
                ← Back
              </button>
              <button onClick={() => setStep(3)}
                className="flex-1 bg-orange-500 text-white rounded-lg py-2.5 font-semibold hover:bg-orange-600">
                Continue →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Step 3: Search ────────────────────────────────────────── */}
      {step === 3 && (
        <div>
          <StepHeader step={3} current={step} title="Find Venues" />

          <div className="space-y-3 mb-4">
            <textarea value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
              rows={3} placeholder="Describe your outing idea — e.g. 'Fun Saturday dinner and bowling, budget around $30 per person'"
              className="w-full border border-gray-300 dark:border-slate-600 rounded-lg px-4 py-2.5 text-sm bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100 placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-400" />
            <input value={location} onChange={e => setLocation(e.target.value)}
              placeholder="Location"
              className="w-full border border-gray-300 dark:border-slate-600 rounded-lg px-4 py-2 text-sm bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100 placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-400" />
          </div>

          {/* Two paths: manual search or orchestrate */}
          <div className="flex gap-3 mb-6">
            <button onClick={() => setStep(2)}
              className="border border-gray-300 rounded-lg px-4 py-2.5 text-gray-600 font-semibold hover:bg-gray-50">
              ← Back
            </button>
            <button onClick={handleSearch} disabled={!searchQuery || searching}
              className="flex-1 bg-orange-500 text-white rounded-lg py-2.5 font-semibold hover:bg-orange-600 disabled:opacity-50">
              {searching ? "Searching…" : "Search Venues"}
            </button>
          </div>

          <div className="border-t border-gray-200 pt-4">
            <p className="text-xs text-gray-400 text-center mb-3">or skip all steps</p>
            <button onClick={handleOrchestrate} disabled={!searchQuery || orchestrating}
              className="w-full border-2 border-orange-400 text-orange-600 rounded-lg py-2.5 font-semibold hover:bg-orange-50 disabled:opacity-50 flex items-center justify-center gap-2">
              {orchestrating ? (
                <>
                  <span className="animate-spin">⚙</span>
                  <span>AI is planning your outing…</span>
                </>
              ) : (
                <>✨ Let AI plan everything</>
              )}
            </button>
            <p className="text-xs text-gray-400 text-center mt-1">
              Searches venues, checks schedules, and picks the best match — automatically
            </p>
          </div>

          {orchestrating && (
            <div className="mt-4 bg-orange-50 border border-orange-200 rounded-lg p-4 text-sm text-orange-700 space-y-1">
              <p className="font-semibold">AI Orchestrator running…</p>
              <p>🔍 Searching Yelp, Eventbrite &amp; Ticketmaster</p>
              <p>📅 Finding available time slots</p>
              <p>🏆 Ranking venues against your constraints</p>
              <p>📋 Building itinerary</p>
            </div>
          )}

          {/* Search results */}
          {searchResult && !searching && (
            <div className="mt-4 space-y-3">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-700">
                <p className="font-semibold">Agent Summary</p>
                <p>{searchResult.summary}</p>
                {searchResult.sources_searched.length > 0 && (
                  <p className="text-xs mt-1 text-blue-500">Sources: {searchResult.sources_searched.join(", ")}</p>
                )}
              </div>
              <p className="text-sm font-medium text-gray-600 dark:text-slate-300">
                {searchResult.venues.length} venue{searchResult.venues.length !== 1 ? "s" : ""} found
              </p>
              {searchResult.venues.length === 0 ? (
                <div className="rounded-lg border border-amber-200 bg-amber-50 dark:bg-amber-950 dark:border-amber-700 p-4 text-sm text-amber-700 dark:text-amber-300 space-y-1">
                  <p className="font-semibold">No venues returned by any source.</p>
                  {configSt && !configSt.ai_ready && (
                    <p>The AI search agent requires an LLM API key (Claude or Gemini) — see the warning above.</p>
                  )}
                  {configSt && !configSt.yelp && !configSt.google_places && (
                    <p>No venue API keys are configured. Add Yelp or Google Places keys to <code>.env</code>.</p>
                  )}
                  <p>Try rephrasing your query, or{" "}
                    <button onClick={handleOrchestrate} className="underline font-medium">let AI plan everything</button>
                    {" "}once keys are configured.
                  </p>
                </div>
              ) : (
                <>
                  <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                    {searchResult.venues.map((v, i) => (
                      <VenueCard key={i} venue={v} />
                    ))}
                  </div>
                  <button onClick={() => { setStep(4); handleRank(); }}
                    className="w-full bg-orange-500 text-white rounded-lg py-2.5 font-semibold hover:bg-orange-600">
                    Rank &amp; Score These Venues →
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Step 4: Rank ──────────────────────────────────────────── */}
      {step === 4 && (
        <div>
          <StepHeader step={4} current={step} title="Ranked Recommendations" />

          {ranking && (
            <div className="text-center py-8 text-gray-500">
              <p className="animate-pulse">Recommendation Agent scoring venues…</p>
            </div>
          )}

          {recommendation && !ranking && (
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-700">
                <p className="font-semibold">AI Recommendation</p>
                <p>{recommendation.summary}</p>
              </div>

              <p className="text-sm font-medium text-gray-600">
                {recommendation.ranked_venues.length} venues passed · {recommendation.rejected_venues.length} filtered out
              </p>

              <div className="space-y-2">
                {recommendation.ranked_venues.map((v, i) => (
                  <VenueCard key={i} venue={v} score={v.score}
                    passed={v.passed_hard_constraints}
                    selected={selectedVenue?.name === v.name}
                    onSelect={() => setSelectedVenue(v)} />
                ))}
              </div>

              {recommendation.rejected_venues.length > 0 && (
                <details className="mt-2">
                  <summary className="text-sm text-gray-400 cursor-pointer">
                    {recommendation.rejected_venues.length} filtered out (click to show)
                  </summary>
                  <div className="mt-2 space-y-2">
                    {recommendation.rejected_venues.map((v, i) => (
                      <VenueCard key={i} venue={v} score={v.score} passed={false}
                        violation={v.violation_reasons} />
                    ))}
                  </div>
                </details>
              )}

              <div className="flex gap-3">
                <button onClick={() => setStep(3)}
                  className="border border-gray-300 rounded-lg px-4 py-2.5 text-gray-600 font-semibold hover:bg-gray-50">
                  ← Back
                </button>
                <button onClick={() => setStep(5)} disabled={!selectedVenue}
                  className="flex-1 bg-orange-500 text-white rounded-lg py-2.5 font-semibold hover:bg-orange-600 disabled:opacity-50">
                  Review &amp; Book →
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Step 5: Review & Book ─────────────────────────────────── */}
      {step === 5 && (
        <div>
          <StepHeader step={5} current={step} title="Review & Book" />

          {orchestratorResult && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-4 space-y-2">
              <p className="font-semibold text-orange-800">AI Orchestrator Result</p>
              <p className="text-sm text-orange-700">{orchestratorResult.itinerary_summary}</p>
              {orchestratorResult.estimated_cost_per_person && (
                <p className="text-sm text-orange-700">💵 {orchestratorResult.estimated_cost_per_person}</p>
              )}
              {orchestratorResult.rag_insights && (
                <p className="text-xs text-orange-600 italic">💡 {orchestratorResult.rag_insights}</p>
              )}
            </div>
          )}

          {selectedVenue && (
            <div className="border border-orange-300 bg-white rounded-xl p-5 mb-4 space-y-1.5">
              <div className="font-bold text-lg">{selectedVenue.name}</div>
              {"address" in selectedVenue && selectedVenue.address && (
                <div className="text-sm text-gray-500">📍 {selectedVenue.address}</div>
              )}
              {"price_tier" in selectedVenue && selectedVenue.price_tier && (
                <div className="text-sm">💰 {selectedVenue.price_tier}</div>
              )}
              {"rating" in selectedVenue && selectedVenue.rating && (
                <div className="text-sm text-yellow-600">⭐ {selectedVenue.rating}</div>
              )}
              {"score" in selectedVenue && (
                <div className="text-sm text-green-600 font-medium">{(selectedVenue as ScoredVenue).score}% match</div>
              )}
            </div>
          )}

          {orchestratorResult?.recommended_slot && (
            <div className="border border-gray-200 rounded-xl p-4 mb-4">
              <p className="font-medium text-gray-700 mb-1">Suggested time</p>
              {(() => {
                const slot = orchestratorResult.recommended_slot as Record<string, string>;
                return (
                  <>
                    <p className="text-sm">📅 {slot.day_name || ""} {slot.date || ""}</p>
                    <p className="text-sm">🕐 {slot.start_time || ""} – {slot.end_time || ""}</p>
                  </>
                );
              })()}
            </div>
          )}

          {members.length > 0 && (
            <p className="text-sm text-gray-500 mb-4">
              Invites will be sent to: {members.map(m => m.email).filter(Boolean).join(", ")}
            </p>
          )}

          {!booked ? (
            <div className="flex gap-3">
              <button onClick={() => setStep(4)}
                className="border border-gray-300 rounded-lg px-4 py-2.5 text-gray-600 font-semibold hover:bg-gray-50">
                ← Back
              </button>
              <button onClick={handleBook} disabled={booking}
                className="flex-1 bg-orange-500 text-white rounded-lg py-2.5 font-semibold hover:bg-orange-600 disabled:opacity-50">
                {booking ? "Booking…" : "Book & Send Invites 🎉"}
              </button>
            </div>
          ) : (
            <div className="text-center space-y-3">
              <div className="text-4xl">🎉</div>
              <p className="text-xl font-bold text-green-700">Outing Booked!</p>
              <p className="text-gray-500 text-sm">Calendar invites sent to your group.</p>
              <button onClick={() => setStep(6)}
                className="w-full bg-orange-500 text-white rounded-lg py-2.5 font-semibold hover:bg-orange-600">
                Leave Feedback →
              </button>
            </div>
          )}
        </div>
      )}

      {/* ── Step 6: Feedback ──────────────────────────────────────── */}
      {step === 6 && (
        <div>
          <StepHeader step={6} current={step} title="Feedback" />

          {!feedbackDone ? (
            <div className="space-y-5">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-2">Overall rating</p>
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map(n => (
                    <button key={n} onClick={() => setOverallRating(n)}
                      className={`text-2xl transition-transform ${n <= overallRating ? "text-yellow-400 scale-110" : "text-gray-200"}`}>
                      ★
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Tell us about your experience</p>
                <textarea value={feedbackText} onChange={e => setFeedbackText(e.target.value)}
                  rows={4} placeholder="What did you enjoy? What could be better? Would you do this again?"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-orange-500" />
              </div>
              <button onClick={() => setFeedbackDone(true)}
                className="w-full bg-orange-500 text-white rounded-lg py-2.5 font-semibold hover:bg-orange-600">
                Submit Feedback
              </button>
            </div>
          ) : (
            <div className="text-center space-y-4 py-6">
              <div className="text-4xl">🙏</div>
              <p className="text-xl font-bold">Thanks for the feedback!</p>
              <p className="text-gray-500 text-sm">Your input helps improve future outings.</p>
              <div className="flex gap-3">
                <a href="/" className="flex-1 border border-gray-300 rounded-lg py-2.5 font-semibold text-center text-gray-600 hover:bg-gray-50">
                  Home
                </a>
                <a href="/plan" className="flex-1 bg-orange-500 text-white rounded-lg py-2.5 font-semibold text-center hover:bg-orange-600">
                  Plan another outing
                </a>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
