"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useAuth } from "@/lib/auth-context";
import { hangouts as hangoutsApi, Hangout, SuggestedMatch } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function SwipePage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [feed, setFeed] = useState<Hangout[]>([]);
  const [index, setIndex] = useState(0);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [matches, setMatches] = useState<SuggestedMatch[]>([]);
  const [creating, setCreating] = useState(false);

  const loadFeed = useCallback(async () => {
    try {
      const data = await hangoutsApi.feed();
      setFeed(data);
      setIndex(0);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    if (!loading && !user) { router.replace("/login"); return; }
    if (user) loadFeed();
  }, [loading, user, router, loadFeed]);

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

    // If interested, try to generate matches
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
        // Update the local match so the link becomes a real href
        setMatches((prev) => prev.map(m => m.id === matchId ? result : m));
        router.push(`/plan?group_id=${result.group_id}`);
      }
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to create group");
    } finally {
      setCreating(false);
    }
  };

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === "ArrowLeft") handleSwipe("pass");
    if (e.key === "ArrowRight") handleSwipe("interested");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index, feed]);

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  if (loading || !user) return <p className="text-center mt-20">Loading...</p>;

  const card = filteredFeed[index];
  const maxCount = Math.max(1, ...Object.values(tagCounts));

  return (
    <div className="min-h-[calc(100vh-80px)] -mx-4 sm:mx-0 rounded-3xl bg-[#04070F] text-white px-4 sm:px-8 py-8 overflow-hidden">
      <div className="max-w-3xl mx-auto relative">
        <div className="absolute inset-0 pointer-events-none">
          <div className="mx-auto mt-10 h-64 w-64 rounded-full bg-[radial-gradient(circle,_rgba(89,135,255,0.35)_0%,_rgba(255,149,0,0.25)_35%,_rgba(167,80,255,0.22)_60%,_rgba(0,0,0,0)_80%)] blur-2xl" />
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold mb-6 text-center tracking-tight relative z-10">Discover Hangouts</h1>

        {/* Suggested matches banner */}
        {matches.length > 0 && (
          <div className="mb-6 relative z-10">
            {matches.map((m) => (
              <div key={m.id} className="bg-green-50 border border-green-300 rounded-lg p-4 mb-2 text-black">
                <p className="font-semibold text-green-800">Match found! ({m.member_user_ids.length} people, score: {m.score})</p>
                <a
                  href={m.group_id ? `/plan?group_id=${m.group_id}` : "#"}
                  onClick={!m.group_id ? async (e) => {
                    e.preventDefault();
                    await handleCreateGroup(m.id);
                  } : undefined}
                  className="mt-2 inline-block bg-green-600 text-white rounded-lg px-4 py-2 font-semibold hover:bg-green-700 disabled:opacity-50"
                >
                  {creating ? "Creating group…" : "🗓 Plan this outing"}
                </a>
              </div>
            ))}
          </div>
        )}

        {/* Bubble tag filters */}
        {allTags.length > 0 && (
          <>
            <p className="text-sm text-[#f1b9bf] text-center mb-2 relative z-10">Describe a vibe or pick suggestions</p>
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
                <button className="text-yellow-300 font-semibold text-sm">Show More</button>
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
          <div className="max-w-2xl mx-auto bg-white border border-gray-200 rounded-3xl p-6 shadow-sm text-black">
            <h2 className="text-4xl font-bold mb-2">{card.title}</h2>
            {card.description && <p className="text-gray-700 text-xl mb-3">{card.description}</p>}
            {card.location_area && (
              <p className="text-3xl font-semibold text-gray-500 mb-3">{card.location_area}</p>
            )}
            {card.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {card.tags.map((tag) => (
                  <span key={tag} className="bg-orange-50 text-orange-600 text-base font-semibold px-4 py-1 rounded-full">
                    {tag}
                  </span>
                ))}
              </div>
            )}
            <div className="flex gap-4 mt-4">
              <button
                onClick={() => handleSwipe("pass")}
                className="flex-1 border-2 border-gray-300 rounded-xl py-3 text-4xl font-semibold text-gray-500 hover:bg-gray-100"
              >
                Pass
              </button>
              <button
                onClick={() => handleSwipe("interested")}
                className="flex-1 bg-orange-500 text-white rounded-xl py-3 text-4xl font-semibold hover:bg-orange-600"
              >
                Interested
              </button>
            </div>
            <p className="text-sm text-gray-400 text-center mt-2">or use arrow keys</p>
          </div>
        ) : (
          <div className="text-center text-gray-300 mt-12">
            <p className="text-4xl mb-2">{selectedTags.length ? "🔎" : "✨"}</p>
            <p>
              {selectedTags.length
                ? "No hangouts match these filters."
                : "No more hangouts to discover right now."}
            </p>
            {selectedTags.length ? (
              <button
                onClick={() => setSelectedTags([])}
                className="mt-4 text-orange-300 font-medium hover:text-orange-200"
              >
                Clear filters
              </button>
            ) : (
              <button onClick={loadFeed} className="mt-4 text-orange-300 font-medium hover:text-orange-200">Refresh feed</button>
            )}
          </div>
        )}

        <p className="text-2xl text-white/70 text-center mt-8">
          {filteredFeed.length > 0 && index < filteredFeed.length ? `${index + 1} / ${filteredFeed.length}` : ""}
        </p>

        <style jsx>{`
          .animate-float {
            animation-name: floatY;
            animation-iteration-count: infinite;
            animation-timing-function: ease-in-out;
          }
          @keyframes floatY {
            0%, 100% {
              transform: translateY(0);
            }
            50% {
              transform: translateY(-10px);
            }
          }
        `}</style>
      </div>
    </div>
  );
}
