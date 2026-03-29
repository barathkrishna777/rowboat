"use client";

import { useAuth } from "@/lib/auth-context";
import { hangouts as hangoutsApi, plans as plansApi, OrchestratorPlan, ScoredVenue } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

const VIBE_SUGGESTIONS = [
  "brunch glow-up",
  "karaoke chaos",
  "late-night dessert",
  "chill coffee catch-up",
  "arcade energy",
  "beer garden",
  "mini golf",
  "live music",
  "museum date",
  "food truck crawl",
];

export default function ChooseVibePage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [vibeKeywords, setVibeKeywords] = useState<string[]>([]);
  const [vibeInput, setVibeInput] = useState("");
  const [result, setResult] = useState<OrchestratorPlan | null>(null);
  const [vibeIndex, setVibeIndex] = useState(0);
  const [loadingResults, setLoadingResults] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const lastRequestId = useRef(0);

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  const triggerOrchestrate = useCallback(async (keywords: string[]) => {
    if (!keywords.length) {
      setResult(null);
      setError(null);
      setVibeIndex(0);
      return;
    }

    const requestId = lastRequestId.current + 1;
    lastRequestId.current = requestId;
    setLoadingResults(true);
    setError(null);
    setVibeIndex(0);

    try {
      const next = await plansApi.orchestrate({
        request: keywords.join(", "),
        location: "Pittsburgh, PA",
      });
      if (lastRequestId.current !== requestId) return;
      setResult(next);
    } catch (err: unknown) {
      if (lastRequestId.current !== requestId) return;
      setResult(null);
      setError(err instanceof Error ? err.message : "Could not load vibe-based suggestions.");
    } finally {
      if (lastRequestId.current === requestId) setLoadingResults(false);
    }
  }, []);

  const addKeyword = useCallback((keyword: string) => {
    const trimmed = keyword.trim();
    if (!trimmed) return;
    const normalized = trimmed.toLowerCase();
    if (vibeKeywords.some((item) => item.toLowerCase() === normalized)) return;
    const next = [...vibeKeywords, trimmed];
    setVibeKeywords(next);
    setVibeInput("");
    void triggerOrchestrate(next);
  }, [triggerOrchestrate, vibeKeywords]);

  const removeKeyword = useCallback((keyword: string) => {
    const next = vibeKeywords.filter((item) => item !== keyword);
    setVibeKeywords(next);
    void triggerOrchestrate(next);
  }, [triggerOrchestrate, vibeKeywords]);

  const handleVibeSwipe = useCallback(async (venue: ScoredVenue, action: "pass" | "interested") => {
    if (action === "interested") {
      try {
        const created = await hangoutsApi.create({
          title: venue.name,
          description: venue.explanation || `${venue.name} at ${venue.address}`,
          tags: venue.categories || [],
          location_area: venue.address,
        });
        await hangoutsApi.swipe(created.id, "interested");
      } catch {
        // Keep the experience moving even if persistence fails.
      }
    }

    setVibeIndex((current) => current + 1);
  }, []);

  if (loading) return <p className="mt-20 text-center text-[var(--text)]">Loading...</p>;
  if (!user) return null;

  const rankedVenues = result?.ranked_venues || [];
  const currentVenue = rankedVenues[vibeIndex];
  const availableSuggestions = VIBE_SUGGESTIONS.filter((item) => !vibeKeywords.includes(item));

  return (
    <div className="-mx-4 -my-8 min-h-[calc(100vh-80px)] overflow-hidden px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-128px)] w-full max-w-[1480px] flex-col">
        <div className="relative flex-1 overflow-hidden rounded-[2rem] border border-[var(--border)] bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.96))] px-4 py-5 shadow-[0_18px_64px_rgba(15,23,42,0.08)] dark:bg-[linear-gradient(180deg,rgba(7,12,24,0.98),rgba(3,5,12,0.96))] dark:shadow-[0_24px_80px_rgba(2,6,23,0.45)] sm:px-8 sm:py-8">
          <div className="absolute inset-0 flex justify-center items-start pointer-events-none">
            <div className="ambient-glow mt-16 h-[420px] w-[780px] rounded-full blur-3xl" />
          </div>

          <div className="relative z-10 flex items-center justify-between gap-4">
            <a href="/discover" className="inline-flex items-center gap-2 text-sm font-medium text-[var(--text-muted)] transition hover:text-[var(--text)]">
              <span className="text-lg leading-none">&larr;</span>
              Back to discover
            </a>
            <a href="/discover/presets" className="text-sm font-semibold text-orange-600 transition hover:text-orange-700 dark:text-orange-200 dark:hover:text-white">
              Need more control? Try presets
            </a>
          </div>

          {vibeKeywords.length === 0 && !loadingResults && rankedVenues.length === 0 && (
            <div className="relative z-10 pb-4 pt-8 text-center">
              <p className="text-[11px] font-semibold uppercase tracking-[0.34em] text-[var(--text-muted)]">
                Mood-first discovery
              </p>
              <h1 className="mt-3 font-['Iowan_Old_Style','Palatino_Linotype','Book_Antiqua','Georgia',serif] text-5xl font-semibold leading-[0.95] text-[var(--text)] sm:text-6xl">
                Choose your vibe
              </h1>
              <p className="mx-auto mt-3 max-w-2xl text-sm leading-7 text-[var(--text-muted)] sm:text-base">
                Tap a bubble or type your own cue, then swipe through spots that match.
              </p>
            </div>
          )}

          {loadingResults && (
            <div className="relative z-10 flex flex-col items-center gap-3 py-16">
              <div className="h-12 w-12 rounded-full border-[3px] border-slate-300 border-t-orange-400 animate-spin dark:border-white/20" />
              <p className="text-sm text-[var(--text-muted)]">Finding places that fit this vibe...</p>
            </div>
          )}

          {!loadingResults && error && (
            <div className="relative z-10 mx-auto mt-8 max-w-2xl rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-200">
              {error}
            </div>
          )}

          {!loadingResults && currentVenue && (
            <div className="relative z-10 mt-8 flex-shrink-0">
              <div className="mx-auto flex w-full max-w-6xl flex-col overflow-hidden rounded-[2rem] border border-[var(--border)] bg-[var(--surface)] shadow-[0_14px_48px_rgba(15,23,42,0.10)] dark:shadow-[0_24px_70px_rgba(2,6,23,0.36)] xl:flex-row">
                {currentVenue.image_url && (
                  <div className="relative h-64 bg-slate-100 xl:h-auto xl:w-[42%] flex-shrink-0 dark:bg-slate-900/40">
                    <img
                      src={currentVenue.image_url}
                      alt={currentVenue.name}
                      className="h-full w-full object-cover"
                      onError={(event) => {
                        event.currentTarget.style.display = "none";
                      }}
                    />
                    <div className="absolute right-3 top-3 rounded-full bg-black/65 px-3 py-1 text-sm font-bold text-white backdrop-blur-sm">
                      {Math.round((currentVenue.score || 0) * 100)}% match
                    </div>
                    {currentVenue.source && (
                      <div className="absolute left-3 top-3 rounded-full bg-white/90 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-600">
                        {currentVenue.source}
                      </div>
                    )}
                  </div>
                )}

                <div className="flex flex-1 flex-col justify-between p-6 xl:p-8">
                  <div>
                    <div className="mb-3 flex items-start justify-between gap-3">
                      <h2 className="font-['Iowan_Old_Style','Palatino_Linotype','Book_Antiqua','Georgia',serif] text-3xl font-semibold leading-tight text-[var(--text)]">
                        {currentVenue.name}
                      </h2>
                      {!currentVenue.image_url && (
                        <span className="rounded-full bg-orange-100 px-3 py-1 text-sm font-bold text-orange-700 dark:bg-orange-500/14 dark:text-orange-200">
                          {Math.round((currentVenue.score || 0) * 100)}%
                        </span>
                      )}
                    </div>

                    {currentVenue.address && (
                      <p className="mb-3 flex items-center gap-1 text-sm text-[var(--text-muted)]">
                        <span className="text-base">&#x1F4CD;</span>
                        {currentVenue.address}
                      </p>
                    )}

                    <div className="mb-4 flex flex-wrap items-center gap-3 text-sm text-[var(--text-muted)]">
                      {currentVenue.rating != null && (
                        <span className="flex items-center gap-1 font-semibold text-amber-600 dark:text-amber-300">
                          <span>&#x2B50;</span>
                          {currentVenue.rating.toFixed(1)}
                        </span>
                      )}
                      {currentVenue.review_count != null && currentVenue.review_count > 0 && (
                        <span>{currentVenue.review_count.toLocaleString()} reviews</span>
                      )}
                      {currentVenue.price_tier && (
                        <span className="font-medium text-emerald-700 dark:text-emerald-300">{currentVenue.price_tier}</span>
                      )}
                    </div>

                    {currentVenue.explanation && (
                      <p className="mb-4 text-sm leading-7 text-[var(--text-muted)]">{currentVenue.explanation}</p>
                    )}

                    {currentVenue.categories && currentVenue.categories.length > 0 && (
                      <div className="mb-4 flex flex-wrap gap-1.5">
                        {currentVenue.categories.map((category) => (
                          <span
                            key={category}
                            className="rounded-full border border-orange-200 bg-orange-50 px-2.5 py-1 text-xs font-semibold text-orange-700 dark:border-orange-500/25 dark:bg-orange-500/10 dark:text-orange-200"
                          >
                            {category}
                          </span>
                        ))}
                      </div>
                    )}

                    {currentVenue.url && (
                      <a
                        href={currentVenue.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-sm font-medium text-orange-600 transition hover:text-orange-700 dark:text-orange-300 dark:hover:text-orange-200"
                      >
                        Open listing <span className="text-xs">&#x2197;</span>
                      </a>
                    )}
                  </div>

                  <div className="mt-6">
                    <div className="flex gap-3">
                      <button
                        onClick={() => void handleVibeSwipe(currentVenue, "pass")}
                        className="flex-1 rounded-xl border border-[var(--border)] py-3 font-semibold text-[var(--text)] transition hover:bg-black/5 dark:hover:bg-white/8"
                      >
                        Pass
                      </button>
                      <button
                        onClick={() => void handleVibeSwipe(currentVenue, "interested")}
                        className="flex-1 rounded-xl bg-orange-500 py-3 font-semibold text-white shadow-md transition hover:bg-orange-600"
                      >
                        Interested
                      </button>
                    </div>
                    <p className="mt-2 text-center text-xs text-[var(--text-muted)]">
                      {vibeIndex + 1} / {rankedVenues.length}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {!loadingResults && vibeKeywords.length > 0 && rankedVenues.length > 0 && !currentVenue && (
            <div className="relative z-10 py-12 text-center text-[var(--text-muted)]">
              <p className="mb-2 text-3xl">&#x2728;</p>
              <p>You&apos;ve seen every spot for this vibe.</p>
              <button
                onClick={() => {
                  setVibeKeywords([]);
                  setResult(null);
                  setVibeInput("");
                  setVibeIndex(0);
                }}
                className="mt-4 font-medium text-orange-600 transition hover:text-orange-700 dark:text-orange-300 dark:hover:text-orange-200"
              >
                Start fresh
              </button>
            </div>
          )}

          <div className="flex-1 min-h-6" />

          <div className="relative z-10 mb-3 w-full overflow-hidden">
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="bubble-strip-glow h-12 w-full max-w-4xl rounded-full blur-2xl" />
            </div>

            <div className="relative flex flex-wrap justify-center gap-2.5 px-2 py-3">
              {availableSuggestions.map((suggestion, index) => {
                const hue = (index * 26) % 360;
                return (
                  <button
                    key={suggestion}
                    onClick={() => addKeyword(suggestion)}
                    className="bubble-suggestion bubble-glow bubble-drop rounded-full px-4 py-2 text-[12px] font-medium transition-all duration-300 hover:scale-105 sm:text-[13px]"
                    style={{
                      animationDelay: `${index * 0.06}s`,
                      boxShadow: `0 0 14px 3px hsla(${hue}, 78%, 65%, 0.20), inset 0 0 10px rgba(255,255,255,0.16)`,
                    }}
                  >
                    {suggestion}
                  </button>
                );
              })}

              {vibeKeywords.map((keyword, index) => (
                <button
                  key={keyword}
                  onClick={() => removeKeyword(keyword)}
                  className="bubble-active bubble-drop rounded-full px-4 py-2 text-sm font-semibold transition-all duration-300"
                  style={{ animationDelay: `${index * 0.05}s` }}
                  title="Remove vibe"
                >
                  {keyword} <span className="ml-1 opacity-60">&times;</span>
                </button>
              ))}
            </div>
          </div>

          <div className="relative z-10 mx-auto w-full max-w-3xl pb-2">
            {vibeKeywords.length > 0 && (
              <div className="mb-3 flex flex-wrap justify-center gap-2">
                {vibeKeywords.map((keyword) => (
                  <span
                    key={`chip-${keyword}`}
                    className="inline-flex items-center gap-1 rounded-full border border-orange-200 bg-orange-50 px-3 py-1 text-xs text-orange-700 dark:border-orange-500/25 dark:bg-orange-500/10 dark:text-orange-200"
                  >
                    {keyword}
                    <button onClick={() => removeKeyword(keyword)} className="opacity-60 transition hover:opacity-100">
                      &times;
                    </button>
                  </span>
                ))}
              </div>
            )}

            <div className="flex gap-2">
              <input
                type="text"
                value={vibeInput}
                onChange={(event) => setVibeInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    addKeyword(vibeInput);
                  }
                }}
                placeholder="Type a vibe... cozy drinks, arcade energy, karaoke chaos"
                className="flex-1 rounded-xl border border-[var(--border)] bg-white/70 px-4 py-3 text-[var(--text)] placeholder:text-[var(--text-muted)] focus:border-orange-300 focus:outline-none focus:ring-1 focus:ring-orange-200 dark:bg-white/8 dark:focus:border-orange-400/40 dark:focus:ring-orange-400/20"
                disabled={loadingResults}
              />
              <button
                onClick={() => addKeyword(vibeInput)}
                disabled={!vibeInput.trim() || loadingResults}
                className="rounded-xl bg-orange-500 px-5 py-3 font-semibold text-white transition hover:bg-orange-600 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Add
              </button>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .ambient-glow {
          background: radial-gradient(
            ellipse,
            rgba(251, 146, 60, 0.12) 0%,
            rgba(125, 211, 252, 0.12) 35%,
            rgba(192, 132, 252, 0.08) 62%,
            transparent 84%
          );
          animation: pulseSlow 4.2s ease-in-out infinite;
        }
        .bubble-strip-glow {
          background: radial-gradient(
            ellipse,
            rgba(251, 146, 60, 0.18) 0%,
            rgba(125, 211, 252, 0.12) 40%,
            rgba(192, 132, 252, 0.08) 70%,
            transparent 100%
          );
          animation: pulseSlow 4.2s ease-in-out infinite;
        }
        .bubble-suggestion {
          color: #334155;
          background: radial-gradient(circle at 35% 35%, rgba(255, 255, 255, 0.88) 0%, rgba(255, 255, 255, 0.62) 55%, rgba(255, 255, 255, 0.4) 100%);
          border: 1px solid rgba(148, 163, 184, 0.24);
          backdrop-filter: blur(10px);
        }
        .bubble-active {
          color: #9a3412;
          background: rgba(251, 146, 60, 0.18);
          border: 1px solid rgba(251, 146, 60, 0.34);
          box-shadow: 0 0 18px 4px rgba(251, 146, 60, 0.16);
          backdrop-filter: blur(10px);
        }
        :global(.dark) .bubble-suggestion {
          color: rgba(255, 255, 255, 0.84);
          background: radial-gradient(circle at 35% 35%, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.04) 55%, transparent 100%);
          border-color: rgba(255, 255, 255, 0.15);
        }
        :global(.dark) .bubble-active {
          color: #fed7aa;
          background: rgba(255, 149, 0, 0.22);
          border-color: rgba(255, 149, 0, 0.44);
          box-shadow: 0 0 20px 5px rgba(255, 149, 0, 0.25);
        }
        .bubble-drop {
          animation:
            dropIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) both,
            gentleFloat 4s ease-in-out 0.6s infinite;
        }
        .bubble-glow {
          animation:
            dropIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) both,
            gentleFloat 4s ease-in-out 0.6s infinite,
            bubbleGlow 3.2s ease-in-out infinite alternate;
        }
        @keyframes pulseSlow {
          0%, 100% { opacity: 0.74; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.08); }
        }
        @keyframes dropIn {
          0% { opacity: 0; transform: translateY(-40px) scale(0.7); }
          100% { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes gentleFloat {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-4px); }
        }
        @keyframes bubbleGlow {
          0% { filter: brightness(0.95); }
          100% { filter: brightness(1.14); }
        }
      `}</style>
    </div>
  );
}
