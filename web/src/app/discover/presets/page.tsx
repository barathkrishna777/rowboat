"use client";

import { useAuth } from "@/lib/auth-context";
import { presets as presetsApi, Preset } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

function PresetCard({
  preset,
  onToggleFavorite,
  busy,
}: {
  preset: Preset;
  onToggleFavorite: (preset: Preset) => void;
  busy: boolean;
}) {
  const chips = [
    ...preset.criteria.activity_preferences,
    ...preset.criteria.cuisine_preferences,
  ].slice(0, 4);

  return (
    <div className="border-t border-[var(--border)] py-5">
      <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0 flex-1">
          <div className="mb-3 flex items-start justify-between gap-3">
            <div>
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--text-muted)]">
                {preset.source === "built_in" ? "Built-in" : preset.source === "ai" ? "AI-shaped" : "Handmade"}
              </p>
              <h3 className="font-['Iowan_Old_Style','Palatino_Linotype','Book_Antiqua','Georgia',serif] text-2xl font-semibold leading-tight text-[var(--text)]">
                {preset.name}
              </h3>
            </div>
            <button
              onClick={() => onToggleFavorite(preset)}
              disabled={busy}
              aria-label={preset.is_favorite ? "Unfavorite preset" : "Favorite preset"}
              className={`text-2xl leading-none transition-colors ${preset.is_favorite ? "text-red-500" : "text-[var(--text-muted)] hover:text-red-400"} disabled:opacity-50`}
            >
              ♥
            </button>
          </div>

          {preset.description && (
            <p className="mb-4 text-sm leading-6 text-[var(--text-muted)]">{preset.description}</p>
          )}

          {chips.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {chips.map((chip) => (
                <span
                  key={chip}
                  className="rounded-full border border-orange-200 bg-orange-50 px-3 py-1 text-xs font-semibold text-orange-700 dark:border-orange-500/25 dark:bg-orange-500/10 dark:text-orange-200"
                >
                  {chip}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center gap-3 xl:flex-col xl:items-end">
          {!preset.is_built_in && (
            <a
              href={`/discover/create/manual?preset_id=${encodeURIComponent(preset.id)}`}
              className="inline-flex rounded-xl border border-[var(--border)] px-4 py-2.5 text-sm font-semibold text-[var(--text)] transition hover:border-orange-300 hover:text-orange-700 dark:hover:border-orange-400/35 dark:hover:text-orange-200"
            >
              Edit
            </a>
          )}
          <a
            href={`/swipe?preset_id=${encodeURIComponent(preset.id)}`}
            className="inline-flex rounded-xl bg-orange-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-orange-600"
          >
            Launch
          </a>
        </div>
      </div>
    </div>
  );
}

export default function PresetsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [presets, setPresets] = useState<Preset[]>([]);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  useEffect(() => {
    if (!user) return;
    presetsApi.list().then(setPresets).catch(() => setPresets([]));
  }, [user]);

  const favorites = useMemo(() => presets.filter((preset) => preset.is_favorite), [presets]);
  const regular = useMemo(() => presets.filter((preset) => !preset.is_favorite), [presets]);

  const toggleFavorite = async (preset: Preset) => {
    setBusyId(preset.id);
    try {
      const updated = await presetsApi.setFavorite(preset.id, !preset.is_favorite);
      setPresets((prev) => prev.map((item) => (item.id === preset.id ? updated : item)));
    } finally {
      setBusyId(null);
    }
  };

  if (loading) return <p className="mt-20 text-center text-[var(--text)]">Loading...</p>;
  if (!user) return null;

  return (
    <div className="-mx-4 -my-8 px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <section className="relative overflow-hidden px-2 py-4 sm:px-4">
          <div className="absolute inset-x-0 top-0 h-36 bg-gradient-to-r from-sky-200/45 via-orange-100/55 to-emerald-100/35 blur-3xl dark:from-sky-500/10 dark:via-orange-500/10 dark:to-emerald-500/8" />
          <div className="relative flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.32em] text-[var(--text-muted)]">
                Presets
              </p>
              <h1 className="font-['Iowan_Old_Style','Palatino_Linotype','Book_Antiqua','Georgia',serif] text-4xl font-semibold leading-tight text-[var(--text)] sm:text-5xl">
                Fast starts, kept tidy.
              </h1>
              <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">
                Pin the good ones. Launch them quickly.
              </p>
            </div>
            <a
              href="/discover/create"
              className="inline-flex w-fit rounded-xl border border-orange-200 bg-orange-50 px-4 py-2.5 text-sm font-semibold text-orange-700 transition hover:bg-orange-100 dark:border-orange-500/25 dark:bg-orange-500/10 dark:text-orange-200 dark:hover:bg-orange-500/16"
            >
              Create preset
            </a>
          </div>
        </section>

        {favorites.length > 0 && (
          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.22em] text-[var(--text-muted)]">
              Favorites
            </h2>
            <div className="grid gap-0">
              {favorites.map((preset) => (
                <PresetCard
                  key={preset.id}
                  preset={preset}
                  onToggleFavorite={toggleFavorite}
                  busy={busyId === preset.id}
                />
              ))}
            </div>
          </section>
        )}

        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.22em] text-[var(--text-muted)]">
            All presets
          </h2>
          {regular.length === 0 ? (
            <div className="border-t border-dashed border-[var(--border)] py-6 text-sm text-[var(--text-muted)]">
              No extra presets yet.
            </div>
          ) : (
            <div className="grid gap-0">
              {regular.map((preset) => (
                <PresetCard
                  key={preset.id}
                  preset={preset}
                  onToggleFavorite={toggleFavorite}
                  busy={busyId === preset.id}
                />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
