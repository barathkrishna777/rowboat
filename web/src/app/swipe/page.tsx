"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import { hangouts as hangoutsApi, Hangout, SuggestedMatch } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function SwipePage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [feed, setFeed] = useState<Hangout[]>([]);
  const [index, setIndex] = useState(0);
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

  const handleSwipe = async (action: "pass" | "interested") => {
    const card = feed[index];
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

  const card = feed[index];

  return (
    <div className="max-w-md mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-center">Discover Hangouts</h1>

      {/* Suggested matches banner */}
      {matches.length > 0 && (
        <div className="mb-6">
          {matches.map((m) => (
            <div key={m.id} className="bg-green-50 dark:bg-green-950/50 border border-green-300 dark:border-green-700 rounded-lg p-4 mb-2">
              <p className="font-semibold text-green-800 dark:text-green-300">🎉 Match found! ({m.member_user_ids.length} people interested)</p>
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

      {/* Swipe card */}
      {card ? (
        <div className="bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm">
          <h2 className="text-xl font-bold mb-2 text-gray-900 dark:text-slate-100">{card.title}</h2>
          {card.description && (
            <p className="text-gray-600 dark:text-slate-300 mb-3 leading-relaxed">{card.description}</p>
          )}
          {card.location_area && (
            <p className="text-sm text-gray-500 dark:text-slate-400 mb-2">📍 {card.location_area}</p>
          )}
          {card.tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {card.tags.map((tag) => (
                <span key={tag} className="bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300 text-xs font-semibold px-3 py-1 rounded-full">
                  {tag}
                </span>
              ))}
            </div>
          )}
          <div className="flex gap-4 mt-4">
            <button
              onClick={() => handleSwipe("pass")}
              className="flex-1 border border-gray-300 dark:border-slate-600 rounded-lg py-3 font-semibold text-gray-600 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-700"
            >
              Pass
            </button>
            <button
              onClick={() => handleSwipe("interested")}
              className="flex-1 bg-orange-500 text-white rounded-lg py-3 font-semibold hover:bg-orange-600"
            >
              Interested ✓
            </button>
          </div>
          <p className="text-xs text-gray-400 dark:text-slate-500 text-center mt-2">or use arrow keys ← →</p>
        </div>
      ) : (
        <div className="text-center text-gray-400 dark:text-slate-500 mt-12">
          <p className="text-4xl mb-2">✨</p>
          <p>No more hangouts to discover right now.</p>
          <button onClick={loadFeed} className="mt-4 text-orange-500 font-medium hover:text-orange-600">Refresh feed</button>
        </div>
      )}

      <p className="text-xs text-gray-400 text-center mt-6">
        {feed.length > 0 && index < feed.length ? `${index + 1} / ${feed.length}` : ""}
      </p>
    </div>
  );
}
