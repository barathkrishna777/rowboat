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

function SuggestionButton({
  label,
  onClick,
  active = false,
}: {
  label: string;
  onClick: () => void;
  active?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full border px-3.5 py-2 text-sm font-medium transition ${
        active
          ? "border-orange-300 bg-orange-100 text-orange-800 dark:border-orange-400/35 dark:bg-orange-500/14 dark:text-orange-200"
          : "border-[var(--border)] bg-[var(--surface)] text-[var(--text)] hover:border-orange-300 hover:text-orange-700 dark:hover:border-orange-400/35 dark:hover:text-orange-200"
      }`}
    >
      {label}
    </button>
  );
}

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

  const resetVibe = useCallback(() => {
    setVibeKeywords([]);
    setVibeInput("");
    setResult(null);
    setError(null);
    setVibeIndex(0);
  }, []);

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
        // Keep the flow moving even if persistence fails.
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
    <div className="-mx-4 -my-8 px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl space-y-5">
        <section className="relative overflow-hidden rounded-[2rem] border border-[var(--border)] bg-[var(--surface)] px-5 py-6 shadow-[0_14px_48px_rgba(15,23,42,0.08)] dark:shadow-[0_22px_72px_rgba(2,6,23,0.35)] sm:px-8">
          <div className="absolute inset-x-0 top-0 h-36 bg-gradient-to-r from-orange-200/45 via-sky-100/50 to-violet-100/35 blur-3xl dark:from-orange-500/10 dark:via-sky-500/10 dark:to-violet-500/8" />

          <div className="relative grid gap-5 xl:grid-cols-[minmax(0,0.92fr)_minmax(0,1.25fr)] xl:items-end">
            <div>
              <div className="mb-3 flex flex-wrap items-center gap-3 text-sm text-[var(--text-muted)]">
                <a href="/discover" className="transition hover:text-[var(--text)]">
                  Back
                </a>
                <span>/</span>
                <a href="/discover/presets" className="transition hover:text-[var(--text)]">
                  Presets
                </a>
              </div>
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.3em] text-[var(--text-muted)]">
                Choose your vibe
              </p>
              <h1 className="font-['Iowan_Old_Style','Palatino_Linotype','Book_Antiqua','Georgia',serif] text-4xl font-semibold leading-tight text-[var(--text)] sm:text-5xl">
                Add a few cues and swipe.
              </h1>
              <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">
                Fast prompts up top. Results stay wide and readable.
              </p>
            </div>

            <div className="space-y-3">
              {vibeKeywords.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {vibeKeywords.map((keyword) => (
                    <SuggestionButton
                      key={keyword}
                      label={`${keyword} ×`}
                      onClick={() => removeKeyword(keyword)}
                      active
                    />
                  ))}
                </div>
              )}

              <div className="flex flex-col gap-2 lg:flex-row">
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
                  placeholder="cozy drinks, arcade energy, karaoke chaos"
                  className="flex-1 rounded-xl border border-[var(--border)] bg-[var(--surface)] px-4 py-3 text-[var(--text)] placeholder:text-[var(--text-muted)] focus:border-orange-300 focus:outline-none dark:focus:border-orange-400/40"
                  disabled={loadingResults}
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => addKeyword(vibeInput)}
                    disabled={!vibeInput.trim() || loadingResults}
                    className="rounded-xl bg-orange-500 px-5 py-3 font-semibold text-white transition hover:bg-orange-600 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Add
                  </button>
                  {vibeKeywords.length > 0 && (
                    <button
                      onClick={resetVibe}
                      className="rounded-xl border border-[var(--border)] px-4 py-3 font-semibold text-[var(--text)] transition hover:border-orange-300 hover:text-orange-700 dark:hover:border-orange-400/35 dark:hover:text-orange-200"
                    >
                      Reset
                    </button>
                  )}
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                {availableSuggestions.map((suggestion) => (
                  <SuggestionButton
                    key={suggestion}
                    label={suggestion}
                    onClick={() => addKeyword(suggestion)}
                  />
                ))}
              </div>
            </div>
          </div>
        </section>

        {loadingResults && (
          <div className="rounded-[1.5rem] border border-[var(--border)] bg-[var(--surface)] px-5 py-5 text-sm text-[var(--text-muted)] shadow-sm">
            Finding spots that match this vibe...
          </div>
        )}

        {!loadingResults && error && (
          <div className="rounded-[1.5rem] border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-200">
            {error}
          </div>
        )}

        {!loadingResults && currentVenue && (
          <section className="overflow-hidden rounded-[2rem] border border-[var(--border)] bg-[var(--surface)] shadow-[0_14px_48px_rgba(15,23,42,0.08)] dark:shadow-[0_22px_72px_rgba(2,6,23,0.28)]">
            <div className="grid xl:grid-cols-[minmax(0,1.2fr)_260px]">
              <div className="grid gap-0 lg:grid-cols-[minmax(260px,0.7fr)_minmax(0,1fr)]">
                <div className="min-h-[250px] bg-slate-100 dark:bg-slate-900/40">
                  {currentVenue.image_url ? (
                    <img
                      src={currentVenue.image_url}
                      alt={currentVenue.name}
                      className="h-full w-full object-cover"
                      onError={(event) => {
                        event.currentTarget.style.display = "none";
                      }}
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center bg-gradient-to-br from-orange-100 via-sky-100 to-emerald-100 text-4xl text-slate-500 dark:from-orange-500/10 dark:via-sky-500/10 dark:to-emerald-500/10 dark:text-slate-400">
                      &#x2728;
                    </div>
                  )}
                </div>

                <div className="p-6">
                  <div className="mb-3 flex flex-wrap items-center gap-2">
                    {currentVenue.source && (
                      <span className="rounded-full border border-[var(--border)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--text-muted)]">
                        {currentVenue.source}
                      </span>
                    )}
                    {currentVenue.price_tier && (
                      <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-200">
                        {currentVenue.price_tier}
                      </span>
                    )}
                  </div>

                  <h2 className="font-['Iowan_Old_Style','Palatino_Linotype','Book_Antiqua','Georgia',serif] text-3xl font-semibold leading-tight text-[var(--text)]">
                    {currentVenue.name}
                  </h2>

                  {currentVenue.address && (
                    <p className="mt-2 text-sm text-[var(--text-muted)]">{currentVenue.address}</p>
                  )}

                  <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-[var(--text-muted)]">
                    {currentVenue.rating != null && <span>&#x2B50; {currentVenue.rating.toFixed(1)}</span>}
                    {currentVenue.review_count != null && currentVenue.review_count > 0 && (
                      <span>{currentVenue.review_count.toLocaleString()} reviews</span>
                    )}
                  </div>

                  {currentVenue.explanation && (
                    <p className="mt-4 text-sm leading-7 text-[var(--text-muted)]">{currentVenue.explanation}</p>
                  )}

                  {currentVenue.categories && currentVenue.categories.length > 0 && (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {currentVenue.categories.map((category) => (
                        <span
                          key={category}
                          className="rounded-full border border-orange-200 bg-orange-50 px-3 py-1 text-xs font-semibold text-orange-700 dark:border-orange-500/25 dark:bg-orange-500/10 dark:text-orange-200"
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
                      className="mt-5 inline-flex items-center gap-1 text-sm font-medium text-orange-600 transition hover:text-orange-700 dark:text-orange-300 dark:hover:text-orange-200"
                    >
                      Open listing <span className="text-xs">&#x2197;</span>
                    </a>
                  )}
                </div>
              </div>

              <div className="border-t border-[var(--border)] p-6 xl:border-l xl:border-t-0">
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--text-muted)]">
                  Match
                </p>
                <p className="mt-2 text-4xl font-semibold text-[var(--text)]">
                  {Math.round((currentVenue.score || 0) * 100)}%
                </p>
                <p className="mt-2 text-sm text-[var(--text-muted)]">
                  {vibeIndex + 1} / {rankedVenues.length}
                </p>

                <div className="mt-6 grid gap-3">
                  <button
                    onClick={() => void handleVibeSwipe(currentVenue, "interested")}
                    className="rounded-xl bg-orange-500 py-3 font-semibold text-white transition hover:bg-orange-600"
                  >
                    Interested
                  </button>
                  <button
                    onClick={() => void handleVibeSwipe(currentVenue, "pass")}
                    className="rounded-xl border border-[var(--border)] py-3 font-semibold text-[var(--text)] transition hover:border-orange-300 hover:text-orange-700 dark:hover:border-orange-400/35 dark:hover:text-orange-200"
                  >
                    Pass
                  </button>
                </div>
              </div>
            </div>
          </section>
        )}

        {!loadingResults && vibeKeywords.length > 0 && rankedVenues.length > 0 && !currentVenue && (
          <div className="rounded-[1.5rem] border border-[var(--border)] bg-[var(--surface)] px-5 py-6 text-sm text-[var(--text-muted)] shadow-sm">
            No more places left for this vibe. Reset and try a new mix.
          </div>
        )}
      </div>
    </div>
  );
}
