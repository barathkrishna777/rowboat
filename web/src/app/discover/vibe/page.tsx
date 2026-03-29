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
  "comedy show",
  "cozy and low-key",
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

  if (loading) return <p className="text-center mt-20 text-[var(--text)]">Loading...</p>;
  if (!user) return null;

  const rankedVenues = result?.ranked_venues || [];
  const currentVenue = rankedVenues[vibeIndex];
  const availableSuggestions = VIBE_SUGGESTIONS.filter((item) => !vibeKeywords.includes(item));

  return (
    <div className="-mx-4 -my-8 min-h-[calc(100vh-80px)] overflow-hidden bg-[#04070F] px-4 py-6 text-white sm:px-6 lg:px-10">
      <div className="mx-auto flex min-h-[calc(100vh-128px)] w-full max-w-[1400px] flex-col">
        <div className="relative flex-1 overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(180deg,rgba(7,12,24,0.98),rgba(3,5,12,0.96))] px-4 py-5 shadow-[0_24px_80px_rgba(2,6,23,0.58)] sm:px-8 sm:py-8">
          <div className="absolute inset-0 flex justify-center items-start pointer-events-none">
            <div className="mt-16 h-[420px] w-[720px] rounded-full bg-[radial-gradient(ellipse,rgba(255,149,0,0.16)_0%,rgba(89,135,255,0.14)_36%,rgba(167,80,255,0.10)_62%,transparent_84%)] blur-3xl animate-pulse-slow" />
          </div>

          <div className="relative z-10 flex items-center justify-between gap-4">
            <a href="/discover" className="inline-flex items-center gap-2 text-sm font-medium text-white/60 transition hover:text-white">
              <span className="text-lg leading-none">&larr;</span>
              Back to discover
            </a>
            <a href="/discover/presets" className="text-sm font-semibold text-orange-200 transition hover:text-white">
              Need more control? Try presets
            </a>
          </div>

          {vibeKeywords.length === 0 && !loadingResults && rankedVenues.length === 0 && (
            <div className="relative z-10 pb-6 pt-10 text-center">
              <p className="text-[11px] font-semibold uppercase tracking-[0.34em] text-white/40">Mood-first discovery</p>
              <h1 className="mt-3 font-['Iowan_Old_Style','Palatino_Linotype','Book_Antiqua','Georgia',serif] text-5xl font-semibold leading-[0.95] sm:text-6xl">
                Choose your vibe!
              </h1>
              <p className="mx-auto mt-4 max-w-2xl text-sm leading-7 text-white/58 sm:text-base">
                Tap a bubble, remix the prompt with your own words, and Rowboat will surface places that match the energy.
              </p>
            </div>
          )}

          {loadingResults && (
            <div className="relative z-10 flex flex-col items-center gap-3 py-16">
              <div className="h-12 w-12 rounded-full border-[3px] border-white/25 border-t-orange-400 animate-spin" />
              <p className="text-sm text-white/60">Finding places that fit this exact mood...</p>
            </div>
          )}

          {!loadingResults && error && (
            <div className="relative z-10 mx-auto mt-8 max-w-2xl rounded-2xl border border-red-400/25 bg-red-500/10 px-5 py-4 text-sm text-red-100">
              {error}
            </div>
          )}

          {!loadingResults && currentVenue && (
            <div className="relative z-10 mt-8 flex-shrink-0">
              <div className="mx-auto flex w-full max-w-5xl flex-col overflow-hidden rounded-[2rem] border border-white/10 bg-white text-black shadow-2xl lg:flex-row">
                {currentVenue.image_url && (
                  <div className="relative h-56 bg-gray-100 lg:h-auto lg:w-[45%] flex-shrink-0">
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
                      <div className="absolute left-3 top-3 rounded-full bg-white/90 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-gray-600">
                        {currentVenue.source}
                      </div>
                    )}
                  </div>
                )}

                <div className="flex flex-1 flex-col justify-between p-6 lg:p-8">
                  <div>
                    <div className="mb-3 flex items-start justify-between gap-3">
                      <h2 className="font-['Iowan_Old_Style','Palatino_Linotype','Book_Antiqua','Georgia',serif] text-3xl font-semibold leading-tight">
                        {currentVenue.name}
                      </h2>
                      {!currentVenue.image_url && (
                        <span className="rounded-full bg-orange-100 px-3 py-1 text-sm font-bold text-orange-700">
                          {Math.round((currentVenue.score || 0) * 100)}%
                        </span>
                      )}
                    </div>

                    {currentVenue.address && (
                      <p className="mb-3 flex items-center gap-1 text-sm text-gray-500">
                        <span className="text-base">&#x1F4CD;</span>
                        {currentVenue.address}
                      </p>
                    )}

                    <div className="mb-4 flex flex-wrap items-center gap-3 text-sm text-gray-500">
                      {currentVenue.rating != null && (
                        <span className="flex items-center gap-1 font-semibold text-amber-600">
                          <span>&#x2B50;</span>
                          {currentVenue.rating.toFixed(1)}
                        </span>
                      )}
                      {currentVenue.review_count != null && currentVenue.review_count > 0 && (
                        <span>{currentVenue.review_count.toLocaleString()} reviews</span>
                      )}
                      {currentVenue.price_tier && (
                        <span className="font-medium text-emerald-700">{currentVenue.price_tier}</span>
                      )}
                    </div>

                    {currentVenue.explanation && (
                      <p className="mb-4 text-sm leading-7 text-gray-600">{currentVenue.explanation}</p>
                    )}

                    {currentVenue.categories && currentVenue.categories.length > 0 && (
                      <div className="mb-4 flex flex-wrap gap-1.5">
                        {currentVenue.categories.map((category) => (
                          <span
                            key={category}
                            className="rounded-full bg-orange-50 px-2.5 py-1 text-xs font-semibold text-orange-700"
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
                        className="inline-flex items-center gap-1 text-sm font-medium text-orange-500 transition hover:text-orange-600"
                      >
                        Open source listing <span className="text-xs">&#x2197;</span>
                      </a>
                    )}
                  </div>

                  <div className="mt-6">
                    <div className="flex gap-3">
                      <button
                        onClick={() => void handleVibeSwipe(currentVenue, "pass")}
                        className="flex-1 rounded-xl border-2 border-gray-200 py-3 font-semibold text-gray-500 transition hover:bg-gray-100"
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
                    <p className="mt-2 text-center text-xs text-gray-400">
                      {vibeIndex + 1} / {rankedVenues.length}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {!loadingResults && vibeKeywords.length > 0 && rankedVenues.length > 0 && !currentVenue && (
            <div className="relative z-10 py-12 text-center text-white/55">
              <p className="mb-2 text-3xl">&#x2728;</p>
              <p>You’ve seen every spot for this vibe.</p>
              <button
                onClick={() => {
                  setVibeKeywords([]);
                  setResult(null);
                  setVibeInput("");
                  setVibeIndex(0);
                }}
                className="mt-4 font-medium text-orange-300 transition hover:text-orange-200"
              >
                Start fresh
              </button>
            </div>
          )}

          <div className="relative z-10 flex-1 min-h-8" />

          <div className="relative z-10 mb-3 w-full overflow-hidden">
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="h-12 w-full max-w-3xl rounded-full bg-[radial-gradient(ellipse,rgba(255,149,0,0.2)_0%,rgba(89,135,255,0.15)_40%,rgba(167,80,255,0.1)_70%,transparent_100%)] blur-2xl animate-pulse-slow" />
            </div>

            <div className="relative flex flex-wrap justify-center gap-2.5 px-2 py-3">
              {availableSuggestions.map((suggestion, index) => {
                const hue = (index * 27) % 360;
                return (
                  <button
                    key={suggestion}
                    onClick={() => addKeyword(suggestion)}
                    className="bubble-glow bubble-drop rounded-full px-4 py-2 text-[12px] font-medium text-white/84 backdrop-blur-sm transition-all duration-300 hover:scale-105 hover:text-white sm:text-[13px]"
                    style={{
                      animationDelay: `${index * 0.06}s`,
                      background: "radial-gradient(circle at 35% 35%, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0.04) 50%, transparent 70%)",
                      border: "1px solid rgba(255,255,255,0.15)",
                      boxShadow: `0 0 14px 3px hsla(${hue}, 80%, 65%, 0.24), inset 0 0 8px rgba(255,255,255,0.06)`,
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
                  className="bubble-drop rounded-full px-4 py-2 text-sm font-semibold text-white transition-all duration-300 hover:bg-red-500/30"
                  style={{
                    animationDelay: `${index * 0.05}s`,
                    background: "rgba(255,149,0,0.25)",
                    border: "1px solid rgba(255,149,0,0.52)",
                    boxShadow: "0 0 20px 5px rgba(255,149,0,0.3), 0 0 8px 2px rgba(255,200,100,0.15)",
                  }}
                  title="Remove vibe"
                >
                  {keyword} <span className="ml-1 opacity-60">&times;</span>
                </button>
              ))}
            </div>
          </div>

          <div className="relative z-10 mx-auto w-full max-w-2xl pb-2">
            {vibeKeywords.length > 0 && (
              <div className="mb-3 flex flex-wrap justify-center gap-2">
                {vibeKeywords.map((keyword) => (
                  <span
                    key={`chip-${keyword}`}
                    className="inline-flex items-center gap-1 rounded-full border border-orange-400/30 bg-orange-500/15 px-3 py-1 text-xs text-orange-200"
                  >
                    {keyword}
                    <button onClick={() => removeKeyword(keyword)} className="text-orange-300/60 transition hover:text-red-300">
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
                className="flex-1 rounded-xl border border-white/20 bg-white/10 px-4 py-3 text-white placeholder:text-white/38 focus:border-orange-400/60 focus:outline-none focus:ring-1 focus:ring-orange-400/30"
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
        .animate-pulse-slow { animation: pulseSlow 4s ease-in-out infinite; }
        @keyframes pulseSlow {
          0%, 100% { opacity: 0.72; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.08); }
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
            bubbleGlow 3s ease-in-out infinite alternate;
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
          0% { filter: brightness(0.9); }
          100% { filter: brightness(1.22); }
        }
      `}</style>
    </div>
  );
}
