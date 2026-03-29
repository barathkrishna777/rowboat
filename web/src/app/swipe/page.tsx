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
    <div className="max-w-md mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-center">Discover Hangouts</h1>

      {/* Suggested matches banner */}
      {matches.length > 0 && (
        <div className="mb-6">
          {matches.map((m) => (
            <div key={m.id} className="bg-green-50 border border-green-300 rounded-lg p-4 mb-2">
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
          <p className="text-sm text-gray-500 mb-2">Pick your vibe</p>
          <div className="relative h-64 rounded-2xl border border-gray-200 bg-gradient-to-br from-slate-50 via-white to-orange-50 overflow-hidden mb-4">
            {allTags.map((tag, i) => {
              const isActive = selectedTags.includes(tag);
              const freq = tagCounts[tag] || 1;
              const size = 70 + Math.floor((60 * freq) / maxCount);
              const col = i % 4;
              const row = Math.floor(i / 4);
              const baseLeft = 8 + col * 22;
              const baseTop = 8 + row * 24;
              const left = Math.max(3, Math.min(84, isActive ? 36 + (i % 3) * 10 : baseLeft));
              const top = Math.max(3, Math.min(72, isActive ? 22 + (i % 4) * 11 : baseTop));
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
                      ? "bg-orange-500 text-white border-2 border-orange-500 shadow-[0_8px_24px_rgba(249,115,22,0.35)] scale-110 z-20"
                      : "bg-white text-gray-500 border-2 border-gray-200 opacity-60 hover:opacity-100"
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

          <div className="flex flex-wrap gap-2 mb-4">
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
                  className={`rounded-full px-3 py-1 text-xs font-semibold border ${
                    active
                      ? "bg-orange-500 text-white border-orange-500"
                      : "bg-white text-gray-500 border-gray-200 hover:border-orange-300"
                  }`}
                >
                  {tag}
                </button>
              );
            })}
          </div>
        </>
      )}

      {/* Swipe card */}
      {card ? (
        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
          <h2 className="text-xl font-bold mb-2">{card.title}</h2>
          {card.description && <p className="text-gray-600 mb-3">{card.description}</p>}
          {card.location_area && (
            <p className="text-sm text-gray-500 mb-2">{card.location_area}</p>
          )}
          {card.tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {card.tags.map((tag) => (
                <span key={tag} className="bg-orange-50 text-orange-600 text-xs font-semibold px-3 py-1 rounded-full">
                  {tag}
                </span>
              ))}
            </div>
          )}
          <div className="flex gap-4 mt-4">
            <button
              onClick={() => handleSwipe("pass")}
              className="flex-1 border border-gray-300 rounded-lg py-3 font-semibold text-gray-500 hover:bg-gray-100"
            >
              Pass
            </button>
            <button
              onClick={() => handleSwipe("interested")}
              className="flex-1 bg-orange-500 text-white rounded-lg py-3 font-semibold hover:bg-orange-600"
            >
              Interested
            </button>
          </div>
          <p className="text-xs text-gray-400 text-center mt-2">or use arrow keys</p>
        </div>
      ) : (
        <div className="text-center text-gray-400 mt-12">
          <p className="text-4xl mb-2">{selectedTags.length ? "🔎" : "✨"}</p>
          <p>
            {selectedTags.length
              ? "No hangouts match these filters."
              : "No more hangouts to discover right now."}
          </p>
          {selectedTags.length ? (
            <button
              onClick={() => setSelectedTags([])}
              className="mt-4 text-orange-500 font-medium hover:text-orange-600"
            >
              Clear filters
            </button>
          ) : (
            <button onClick={loadFeed} className="mt-4 text-orange-500 font-medium hover:text-orange-600">Refresh feed</button>
          )}
        </div>
      )}

      <p className="text-xs text-gray-400 text-center mt-6">
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
            transform: translateY(-8px);
          }
        }
      `}</style>
    </div>
  );
}
