"use client";

import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { useAuth } from "@/lib/auth-context";
import {
  hangouts as hangoutsApi,
  plans as plansApi,
  Hangout,
  SuggestedMatch,
  OrchestratorPlan,
  ScoredVenue,
} from "@/lib/api";
import { useRouter } from "next/navigation";

type Mode = "landing" | "vibe_input" | "custom_preset";

const VIBE_SUGGESTIONS = [
  "bowling", "brunch", "nightlife", "hiking", "karaoke",
  "trivia", "coffee", "live music", "escape room", "arcade",
  "beer garden", "comedy show", "museum", "mini golf", "food truck",
];

export default function SwipePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  // Mode
  const [mode, setMode] = useState<Mode>("landing");

  // Custom Preset state (existing bubble-filter flow)
  const [feed, setFeed] = useState<Hangout[]>([]);
  const [index, setIndex] = useState(0);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [matches, setMatches] = useState<SuggestedMatch[]>([]);
  const [creating, setCreating] = useState(false);

  // Pick Your Vibe state
  const [vibeKeywords, setVibeKeywords] = useState<string[]>([]);
  const [vibeInput, setVibeInput] = useState("");
  const [orchestratorResult, setOrchestratorResult] = useState<OrchestratorPlan | null>(null);
  const [vibeLoading, setVibeLoading] = useState(false);
  const [vibeIndex, setVibeIndex] = useState(0);
  const orchestrateAbort = useRef<AbortController | null>(null);

  // Auth guard
  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  // ── Custom Preset helpers ──────────────────────────────────────────

  const loadFeed = useCallback(async () => {
    try {
      const data = await hangoutsApi.feed();
      setFeed(data);
      setIndex(0);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    if (user && mode === "custom_preset") loadFeed();
  }, [user, mode, loadFeed]);

  const { allTags, tagCounts } = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const item of feed) {
      for (const tag of item.tags || []) {
        counts[tag] = (counts[tag] || 0) + 1;
      }
    }
    return {
      allTags: Object.keys(counts).sort((a, b) => a.localeCompare(b)),
      tagCounts: counts,
    };
  }, [feed]);

  const filteredFeed = useMemo(() => {
    if (!selectedTags.length) return feed;
    const selectedSet = new Set(selectedTags);
    return feed.filter((item) => item.tags.some((tag) => selectedSet.has(tag)));
  }, [feed, selectedTags]);

  useEffect(() => {
    setIndex(0);
  }, [selectedTags, feed.length]);

  const handleSwipe = async (action: "pass" | "interested") => {
    const card = filteredFeed[index];
    if (!card) return;
    await hangoutsApi.swipe(card.id, action);
    if (action === "interested") {
      try {
        const m = await hangoutsApi.generateMatches(card.id);
        if (m.length > 0) setMatches((prev) => [...prev, ...m]);
      } catch { /* ok */ }
    }
    setIndex((i) => i + 1);
  };

  const handleCreateGroup = async (matchId: string) => {
    setCreating(true);
    try {
      const result = await hangoutsApi.createGroupFromMatch(matchId);
      if (result.group_id) {
        setMatches((prev) => prev.map((m) => (m.id === matchId ? result : m)));
        router.push(`/plan?group_id=${result.group_id}`);
      }
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to create group");
    } finally {
      setCreating(false);
    }
  };

  // Arrow-key swipe for custom_preset mode
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (mode !== "custom_preset") return;
      if (e.key === "ArrowLeft") handleSwipe("pass");
      if (e.key === "ArrowRight") handleSwipe("interested");
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [index, feed, mode],
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  // ── Vibe helpers ───────────────────────────────────────────────────

  const triggerOrchestrate = useCallback(async (keywords: string[]) => {
    if (!keywords.length) {
      setOrchestratorResult(null);
      return;
    }
    if (orchestrateAbort.current) orchestrateAbort.current.abort();
    orchestrateAbort.current = new AbortController();

    setVibeLoading(true);
    setVibeIndex(0);
    try {
      const result = await plansApi.orchestrate({
        request: keywords.join(", "),
        location: "Pittsburgh, PA",
      });
      setOrchestratorResult(result);
    } catch {
      setOrchestratorResult(null);
    } finally {
      setVibeLoading(false);
    }
  }, []);

  const addKeyword = (kw: string) => {
    const trimmed = kw.trim();
    if (!trimmed || vibeKeywords.includes(trimmed)) return;
    const next = [...vibeKeywords, trimmed];
    setVibeKeywords(next);
    setVibeInput("");
    triggerOrchestrate(next);
  };

  const removeKeyword = (kw: string) => {
    const next = vibeKeywords.filter((k) => k !== kw);
    setVibeKeywords(next);
    triggerOrchestrate(next);
  };

  const handleVibeSwipe = async (venue: ScoredVenue, action: "pass" | "interested") => {
    if (action === "interested") {
      try {
        const created = await hangoutsApi.create({
          title: venue.name,
          description: venue.explanation || `${venue.name} at ${venue.address}`,
          tags: venue.categories || [],
          location_area: venue.address,
        });
        await hangoutsApi.swipe(created.id, "interested");
      } catch { /* ok */ }
    }
    setVibeIndex((i) => i + 1);
  };

  // ── Render guards ──────────────────────────────────────────────────

  if (loading || !user) return <p className="text-center mt-20 text-white">Loading...</p>;

  // ── Shared components ──────────────────────────────────────────────

  const GlowBlob = ({ size = "h-72 w-72" }: { size?: string }) => (
    <div className="absolute inset-0 flex justify-center pointer-events-none">
      <div
        className={`mt-16 ${size} rounded-full bg-[radial-gradient(circle,_rgba(89,135,255,0.4)_0%,_rgba(255,149,0,0.3)_30%,_rgba(167,80,255,0.25)_55%,_rgba(0,0,0,0)_80%)] blur-3xl animate-pulse-slow`}
      />
    </div>
  );

  const BackButton = () => (
    <button
      onClick={() => {
        setMode("landing");
        setVibeKeywords([]);
        setOrchestratorResult(null);
        setVibeInput("");
        setVibeIndex(0);
      }}
      className="absolute top-0 left-0 z-30 text-white/60 hover:text-white transition text-sm font-medium flex items-center gap-1"
    >
      <span className="text-lg">&larr;</span> Back
    </button>
  );

  // ── LANDING ────────────────────────────────────────────────────────

  if (mode === "landing") {
    return (
      <div className="min-h-[calc(100vh-80px)] -mx-4 sm:mx-0 rounded-3xl bg-[#04070F] text-white px-4 sm:px-8 py-12 overflow-hidden">
        <div className="max-w-3xl mx-auto relative">
          <GlowBlob size="h-80 w-80" />

          <div className="relative z-10 flex flex-col items-center pt-20 pb-12">
            <h1 className="text-5xl sm:text-6xl font-bold text-center tracking-tight mb-3 bg-gradient-to-r from-blue-300 via-orange-200 to-purple-300 bg-clip-text text-transparent">
              Choose Your Vibe
            </h1>
            <p className="text-white/50 text-lg mb-16">How do you want to discover?</p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 w-full max-w-lg">
              {/* Pick Your Vibe card */}
              <button
                onClick={() => setMode("vibe_input")}
                className="group relative bg-white/[0.06] backdrop-blur-sm border border-white/10 rounded-2xl p-8 text-center hover:border-orange-400/50 hover:bg-white/[0.09] transition-all duration-300"
              >
                <div className="text-5xl mb-4">&#x2728;</div>
                <h2 className="text-xl font-bold mb-2">Pick Your Vibe</h2>
                <p className="text-sm text-white/50">Type what you feel like and we&apos;ll find matching plans</p>
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-orange-500/0 to-purple-500/0 group-hover:from-orange-500/5 group-hover:to-purple-500/5 transition-all duration-300" />
              </button>

              {/* Custom Preset card */}
              <button
                onClick={() => setMode("custom_preset")}
                className="group relative bg-white/[0.06] backdrop-blur-sm border border-white/10 rounded-2xl p-8 text-center hover:border-blue-400/50 hover:bg-white/[0.09] transition-all duration-300"
              >
                <div className="text-5xl mb-4">&#x1F3AF;</div>
                <h2 className="text-xl font-bold mb-2">Custom Preset</h2>
                <p className="text-sm text-white/50">Browse and filter from curated hangout categories</p>
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-500/0 to-cyan-500/0 group-hover:from-blue-500/5 group-hover:to-cyan-500/5 transition-all duration-300" />
              </button>
            </div>
          </div>
        </div>

        <style jsx>{`
          .animate-pulse-slow { animation: pulseSlow 4s ease-in-out infinite; }
          @keyframes pulseSlow {
            0%, 100% { opacity: 0.7; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.08); }
          }
        `}</style>
      </div>
    );
  }

  // ── VIBE INPUT ─────────────────────────────────────────────────────

  if (mode === "vibe_input") {
    const rankedVenues = orchestratorResult?.ranked_venues || [];
    const currentVenue = rankedVenues[vibeIndex] as ScoredVenue | undefined;
    const availableSuggestions = VIBE_SUGGESTIONS.filter(
      (s) => !vibeKeywords.includes(s),
    );

    return (
      <div className="min-h-[calc(100vh-80px)] -mx-4 sm:mx-0 rounded-3xl bg-[#04070F] text-white px-4 sm:px-8 py-8 overflow-hidden flex flex-col">
        <div className="max-w-3xl mx-auto relative flex-1 flex flex-col">
          <BackButton />
          <GlowBlob />

          {/* ── Top: Venue card with full details ── */}
          <div className="relative z-10 mt-10 flex-shrink-0">
            {vibeLoading && (
              <div className="flex flex-col items-center gap-3 py-16">
                <div className="h-12 w-12 border-3 border-white/30 border-t-orange-400 rounded-full animate-spin" />
                <p className="text-white/60 text-sm">Finding your vibe...</p>
              </div>
            )}

            {vibeKeywords.length === 0 && !vibeLoading && rankedVenues.length === 0 && (
              <div className="py-12 text-center">
                <h2 className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-blue-300 via-orange-200 to-purple-300 bg-clip-text text-transparent">
                  Choose Your Vibe
                </h2>
                <p className="text-white/40 text-sm mt-2">Pick tags below or type your own</p>
              </div>
            )}

            {rankedVenues.length > 0 && !vibeLoading && (
              <>
                {currentVenue ? (
                  <div className="max-w-lg mx-auto bg-white border border-gray-200 rounded-3xl overflow-hidden shadow-xl text-black">
                    {currentVenue.image_url && (
                      <div className="relative w-full h-52 bg-gray-100">
                        <img
                          src={currentVenue.image_url}
                          alt={currentVenue.name}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = "none";
                          }}
                        />
                        <div className="absolute top-3 right-3 bg-black/60 backdrop-blur-sm text-white text-sm font-bold px-3 py-1 rounded-full">
                          {Math.round((currentVenue.score || 0) * 100)}% match
                        </div>
                        {currentVenue.source && (
                          <div className="absolute top-3 left-3 bg-white/90 backdrop-blur-sm text-gray-700 text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full">
                            {currentVenue.source}
                          </div>
                        )}
                      </div>
                    )}
                    <div className="p-5">
                      <div className="flex items-start justify-between mb-1">
                        <h2 className="text-xl font-bold leading-tight">{currentVenue.name}</h2>
                        {!currentVenue.image_url && (
                          <span className="flex-shrink-0 bg-orange-100 text-orange-600 text-sm font-bold px-3 py-1 rounded-full ml-2">
                            {Math.round((currentVenue.score || 0) * 100)}%
                          </span>
                        )}
                      </div>

                      {currentVenue.address && (
                        <p className="text-gray-500 text-sm mb-2 flex items-center gap-1">
                          <span className="text-base">&#x1F4CD;</span> {currentVenue.address}
                        </p>
                      )}

                      <div className="flex items-center gap-3 text-sm text-gray-500 mb-3">
                        {currentVenue.rating != null && (
                          <span className="flex items-center gap-1 font-semibold text-yellow-600">
                            <span>&#x2B50;</span> {currentVenue.rating.toFixed(1)}
                          </span>
                        )}
                        {currentVenue.review_count != null && currentVenue.review_count > 0 && (
                          <span>({currentVenue.review_count.toLocaleString()} reviews)</span>
                        )}
                        {currentVenue.price_tier && (
                          <span className="font-medium text-green-700">{currentVenue.price_tier}</span>
                        )}
                        {!currentVenue.image_url && currentVenue.source && (
                          <span className="text-[10px] uppercase tracking-wider bg-gray-100 px-2 py-0.5 rounded-full font-semibold text-gray-500">
                            {currentVenue.source}
                          </span>
                        )}
                      </div>

                      {currentVenue.explanation && (
                        <p className="text-gray-600 text-sm mb-3 leading-relaxed">{currentVenue.explanation}</p>
                      )}

                      {currentVenue.categories && currentVenue.categories.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mb-3">
                          {currentVenue.categories.map((cat: string) => (
                            <span key={cat} className="bg-orange-50 text-orange-600 text-xs font-semibold px-2.5 py-0.5 rounded-full">
                              {cat}
                            </span>
                          ))}
                        </div>
                      )}

                      {currentVenue.url && (
                        <a
                          href={currentVenue.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-sm text-orange-500 hover:text-orange-600 font-medium mb-3 transition"
                        >
                          View on {currentVenue.source || "web"} <span className="text-xs">&#x2197;</span>
                        </a>
                      )}

                      <div className="flex gap-3 mt-3">
                        <button
                          onClick={() => handleVibeSwipe(currentVenue, "pass")}
                          className="flex-1 border-2 border-gray-300 rounded-xl py-3 font-semibold text-gray-500 hover:bg-gray-100 transition"
                        >
                          Pass
                        </button>
                        <button
                          onClick={() => handleVibeSwipe(currentVenue, "interested")}
                          className="flex-1 bg-orange-500 text-white rounded-xl py-3 font-semibold hover:bg-orange-600 transition shadow-md"
                        >
                          Interested
                        </button>
                      </div>
                      <p className="text-xs text-gray-400 text-center mt-2">
                        {vibeIndex + 1} / {rankedVenues.length}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-white/50 py-12">
                    <p className="text-3xl mb-2">&#x2728;</p>
                    <p>You&apos;ve seen all venues for this vibe!</p>
                    <button
                      onClick={() => {
                        setVibeIndex(0);
                        setOrchestratorResult(null);
                        setVibeKeywords([]);
                      }}
                      className="mt-4 text-orange-300 font-medium hover:text-orange-200 transition"
                    >
                      Start fresh
                    </button>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Spacer */}
          <div className="flex-1 min-h-4" />

          {/* ── Bottom: Glowing suggestion bubbles ── */}
          <div className="relative z-10 mb-4">
            <div className="relative h-56 sm:h-64 flex items-center justify-center">
              {/* Ambient glow behind bubbles */}
              <div className="absolute inset-0 flex justify-center items-center pointer-events-none">
                <div className="w-64 h-32 rounded-full bg-[radial-gradient(ellipse,_rgba(255,149,0,0.25)_0%,_rgba(89,135,255,0.18)_40%,_rgba(167,80,255,0.12)_70%,_transparent_100%)] blur-2xl animate-pulse-slow" />
              </div>

              {availableSuggestions.map((suggestion, i) => {
                const total = availableSuggestions.length;
                const angle = (2 * Math.PI * i) / Math.max(total, 1) - Math.PI / 2;
                const ring = i < 8 ? 0 : 1;
                const radius = ring === 0 ? 110 : 75;
                const x = Math.cos(angle) * radius;
                const y = Math.sin(angle) * radius;
                const size = 60 + ((i * 7) % 24);
                const duration = 4 + (i % 4);
                const delay = (i % 5) * 0.4;
                const hue = (i * 25) % 360;
                return (
                  <button
                    key={`sug-${suggestion}`}
                    onClick={() => addKeyword(suggestion)}
                    className="absolute z-10 rounded-full flex items-center justify-center text-center text-white/80 text-[11px] font-medium backdrop-blur-sm hover:text-white hover:scale-110 transition-all duration-300 animate-float bubble-glow"
                    style={{
                      width: `${size}px`,
                      height: `${size}px`,
                      left: `calc(50% + ${x}px - ${size / 2}px)`,
                      top: `calc(50% + ${y}px - ${size / 2}px)`,
                      animationDuration: `${duration}s`,
                      animationDelay: `${delay}s`,
                      background: `radial-gradient(circle at 35% 35%, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0.04) 50%, transparent 70%)`,
                      border: `1px solid rgba(255,255,255,0.15)`,
                      boxShadow: `0 0 12px 2px hsla(${hue}, 80%, 65%, 0.25), inset 0 0 8px rgba(255,255,255,0.06)`,
                    }}
                  >
                    {suggestion}
                  </button>
                );
              })}

              {vibeKeywords.map((kw, i) => {
                const angle = (2 * Math.PI * i) / Math.max(vibeKeywords.length, 1);
                const radius = 40;
                const x = Math.cos(angle) * radius;
                const y = Math.sin(angle) * radius;
                const duration = 5 + (i % 3);
                return (
                  <button
                    key={kw}
                    onClick={() => removeKeyword(kw)}
                    className="absolute z-20 backdrop-blur-md text-white rounded-full px-4 py-2 text-sm font-semibold hover:bg-red-500/30 hover:border-red-400/50 transition-all duration-300 animate-float"
                    style={{
                      left: `calc(50% + ${x}px - 40px)`,
                      top: `calc(50% + ${y}px - 16px)`,
                      animationDuration: `${duration}s`,
                      animationDelay: `${i * 0.2}s`,
                      background: `rgba(255,149,0,0.2)`,
                      border: `1px solid rgba(255,149,0,0.5)`,
                      boxShadow: `0 0 18px 4px rgba(255,149,0,0.3), 0 0 6px 1px rgba(255,200,100,0.15)`,
                    }}
                    title="Click to remove"
                  >
                    {kw} <span className="ml-1 opacity-60">&times;</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* ── Bottom: keyword chips + text input ── */}
          <div className="max-w-md mx-auto w-full relative z-10 pb-4">
            {vibeKeywords.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {vibeKeywords.map((kw) => (
                  <span
                    key={`chip-${kw}`}
                    className="inline-flex items-center gap-1 bg-orange-500/15 border border-orange-400/30 rounded-full px-3 py-1 text-xs text-orange-200"
                  >
                    {kw}
                    <button onClick={() => removeKeyword(kw)} className="text-orange-300/60 hover:text-red-400 transition">&times;</button>
                  </span>
                ))}
              </div>
            )}
            <div className="flex gap-2">
              <input
                type="text"
                value={vibeInput}
                onChange={(e) => setVibeInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addKeyword(vibeInput);
                  }
                }}
                placeholder="Type a vibe... (e.g. chill, beer party, bowling)"
                className="flex-1 bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/40 focus:outline-none focus:border-orange-400/60 focus:ring-1 focus:ring-orange-400/30 transition"
                disabled={vibeLoading}
              />
              <button
                onClick={() => addKeyword(vibeInput)}
                disabled={!vibeInput.trim() || vibeLoading}
                className="bg-orange-500 hover:bg-orange-600 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl px-5 py-3 font-semibold transition"
              >
                Add
              </button>
            </div>
          </div>
        </div>

        <style jsx>{`
          .animate-pulse-slow { animation: pulseSlow 4s ease-in-out infinite; }
          @keyframes pulseSlow {
            0%, 100% { opacity: 0.7; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.08); }
          }
          .animate-float {
            animation-name: floatY;
            animation-iteration-count: infinite;
            animation-timing-function: ease-in-out;
          }
          @keyframes floatY {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
          }
          .bubble-glow {
            animation: floatY var(--dur, 5s) ease-in-out infinite, bubbleGlow 3s ease-in-out infinite alternate;
          }
          @keyframes bubbleGlow {
            0% { filter: brightness(0.9); }
            100% { filter: brightness(1.2); }
          }
        `}</style>
      </div>
    );
  }

  // ── CUSTOM PRESET ──────────────────────────────────────────────────

  const card = filteredFeed[index];
  const maxCount = Math.max(1, ...(Object.values(tagCounts) as number[]));

  return (
    <div className="min-h-[calc(100vh-80px)] -mx-4 sm:mx-0 rounded-3xl bg-[#04070F] text-white px-4 sm:px-8 py-8 overflow-hidden">
      <div className="max-w-3xl mx-auto relative">
        <BackButton />
        <GlowBlob />

        <h1 className="text-4xl sm:text-5xl font-bold mb-6 text-center tracking-tight relative z-10 pt-6">
          Custom Preset
        </h1>

        {/* Suggested matches banner */}
        {matches.length > 0 && (
          <div className="mb-6 relative z-10">
            {matches.map((m) => (
              <div key={m.id} className="bg-green-50 border border-green-300 rounded-lg p-4 mb-2 text-black">
                <p className="font-semibold text-green-800">
                  Match found! ({m.member_user_ids.length} people, score: {m.score})
                </p>
                <a
                  href={m.group_id ? `/plan?group_id=${m.group_id}` : "#"}
                  onClick={
                    !m.group_id
                      ? async (e: React.MouseEvent) => {
                          e.preventDefault();
                          await handleCreateGroup(m.id);
                        }
                      : undefined
                  }
                  className="mt-2 inline-block bg-green-600 text-white rounded-lg px-4 py-2 font-semibold hover:bg-green-700"
                >
                  {creating ? "Creating group\u2026" : "\uD83D\uDCC5 Plan this outing"}
                </a>
              </div>
            ))}
          </div>
        )}

        {/* Bubble tag filters */}
        {allTags.length > 0 && (
          <>
            <p className="text-sm text-[#f1b9bf] text-center mb-2 relative z-10">
              Pick tags to filter hangouts
            </p>
            <div className="relative h-72 rounded-3xl border border-white/10 bg-black/35 overflow-hidden mb-6 backdrop-blur-sm">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_rgba(111,165,255,0.22)_0%,_rgba(255,181,83,0.15)_30%,_rgba(176,104,255,0.14)_55%,_rgba(0,0,0,0)_75%)]" />
              {allTags.map((tag, i) => {
                const isActive = selectedTags.includes(tag);
                const freq = tagCounts[tag] || 1;
                const size = 68 + Math.floor((52 * freq) / maxCount);
                const col = i % 5;
                const row = Math.floor(i / 5);
                const baseLeft = 4 + col * 19;
                const baseTop = 10 + row * 23;
                const left = Math.max(2, Math.min(86, isActive ? 34 + (i % 3) * 12 : baseLeft));
                const top = Math.max(4, Math.min(72, isActive ? 24 + (i % 4) * 10 : baseTop));
                const duration = 4 + (i % 5);
                const delay = (i % 3) * 0.3;
                return (
                  <button
                    key={tag}
                    onClick={() =>
                      setSelectedTags((prev) =>
                        prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag],
                      )
                    }
                    className={`absolute rounded-full text-xs font-semibold px-2 text-center transition-all duration-500 ease-out animate-float ${
                      isActive
                        ? "bg-white/20 text-white border border-white/40 shadow-[0_10px_30px_rgba(255,255,255,0.2)] scale-110 z-20"
                        : "bg-white/5 text-white/80 border border-white/15 opacity-80 hover:opacity-100"
                    }`}
                    style={
                      {
                        width: `${size}px`,
                        height: `${size}px`,
                        left: `${left}%`,
                        top: `${top}%`,
                        animationDuration: `${duration}s`,
                        animationDelay: `${delay}s`,
                      } as React.CSSProperties
                    }
                  >
                    {tag}
                  </button>
                );
              })}
            </div>

            <div className="mb-8">
              <div className="flex items-center justify-between mb-2">
                <p className="text-white/80 font-semibold">Suggestions</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {allTags.map((tag) => {
                  const active = selectedTags.includes(tag);
                  return (
                    <button
                      key={`chip-${tag}`}
                      onClick={() =>
                        setSelectedTags((prev) =>
                          prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag],
                        )
                      }
                      className={`rounded-full px-3 py-1.5 text-xs font-semibold border transition ${
                        active
                          ? "bg-white text-black border-white"
                          : "bg-white/10 text-white border-white/20 hover:bg-white/20"
                      }`}
                    >
                      {tag}
                    </button>
                  );
                })}
              </div>
            </div>
          </>
        )}

        {/* Swipe card */}
        {card ? (
          <div className="max-w-lg mx-auto bg-white border border-gray-200 rounded-3xl p-6 shadow-sm text-black relative z-10">
            <h2 className="text-2xl font-bold mb-2">{card.title}</h2>
            {card.description && <p className="text-gray-600 mb-3">{card.description}</p>}
            {card.location_area && (
              <p className="text-sm text-gray-500 mb-2">{card.location_area}</p>
            )}
            {card.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {card.tags.map((tag) => (
                  <span
                    key={tag}
                    className="bg-orange-50 text-orange-600 text-xs font-semibold px-3 py-1 rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
            <div className="flex gap-4 mt-4">
              <button
                onClick={() => handleSwipe("pass")}
                className="flex-1 border-2 border-gray-300 rounded-xl py-3 font-semibold text-gray-500 hover:bg-gray-100 transition"
              >
                Pass
              </button>
              <button
                onClick={() => handleSwipe("interested")}
                className="flex-1 bg-orange-500 text-white rounded-xl py-3 font-semibold hover:bg-orange-600 transition"
              >
                Interested
              </button>
            </div>
            <p className="text-xs text-gray-400 text-center mt-2">or use arrow keys</p>
          </div>
        ) : (
          <div className="text-center text-white/50 mt-12 relative z-10">
            <p className="text-4xl mb-2">{selectedTags.length ? "\uD83D\uDD0E" : "\u2728"}</p>
            <p>
              {selectedTags.length
                ? "No hangouts match these filters."
                : "No more hangouts to discover right now."}
            </p>
            {selectedTags.length ? (
              <button
                onClick={() => setSelectedTags([])}
                className="mt-4 text-orange-300 font-medium hover:text-orange-200 transition"
              >
                Clear filters
              </button>
            ) : (
              <button
                onClick={loadFeed}
                className="mt-4 text-orange-300 font-medium hover:text-orange-200 transition"
              >
                Refresh feed
              </button>
            )}
          </div>
        )}

        <p className="text-sm text-white/40 text-center mt-6 relative z-10">
          {filteredFeed.length > 0 && index < filteredFeed.length
            ? `${index + 1} / ${filteredFeed.length}`
            : ""}
        </p>
      </div>

      <style jsx>{`
        .animate-pulse-slow { animation: pulseSlow 4s ease-in-out infinite; }
        @keyframes pulseSlow {
          0%, 100% { opacity: 0.7; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.08); }
        }
        .animate-float {
          animation-name: floatY;
          animation-iteration-count: infinite;
          animation-timing-function: ease-in-out;
        }
        @keyframes floatY {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }
      `}</style>
    </div>
  );
}
