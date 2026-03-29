"use client";

import { useAuth } from "@/lib/auth-context";
import { presets as presetsApi, Preset } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

function PresetCard({ preset, onToggleFavorite, busy }: { preset: Preset; onToggleFavorite: (preset: Preset) => void; busy: boolean; }) {
  const chips = [
    ...preset.criteria.activity_preferences,
    ...preset.criteria.cuisine_preferences,
  ].slice(0, 4);

  return (
    <div className="rounded-[1.75rem] border border-white/10 bg-white/[0.05] p-5 shadow-[0_18px_60px_rgba(7,10,20,0.22)] backdrop-blur-sm">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div>
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.28em] text-orange-300/70">
            {preset.source === "built_in" ? "Built-in" : preset.source === "ai" ? "AI-shaped" : "Handmade"}
          </p>
          <h3 className="font-['Iowan_Old_Style','Palatino_Linotype','Book_Antiqua','Georgia',serif] text-2xl font-semibold text-white">
            {preset.name}
          </h3>
        </div>
        <button
          onClick={() => onToggleFavorite(preset)}
          disabled={busy}
          aria-label={preset.is_favorite ? "Unfavorite preset" : "Favorite preset"}
          className={`text-2xl leading-none transition-colors ${preset.is_favorite ? "text-red-400" : "text-white/35 hover:text-red-300"} disabled:opacity-50`}
        >
          ♥
        </button>
      </div>
      <p className="mb-4 text-sm leading-6 text-white/68">{preset.description || "A sharper starting point for your next outing."}</p>
      <div className="flex flex-wrap gap-2 mb-4">
        {chips.map((chip) => (
          <span key={chip} className="rounded-full border border-orange-400/20 bg-orange-500/12 px-3 py-1 text-xs font-semibold text-orange-100">
            {chip}
          </span>
        ))}
      </div>
      <a href={`/swipe?preset_id=${encodeURIComponent(preset.id)}`} className="inline-block rounded-xl bg-orange-500 px-4 py-2.5 font-semibold text-white transition hover:bg-orange-600">
        Launch this preset
      </a>
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

  const favorites = useMemo(() => presets.filter((p) => p.is_favorite), [presets]);
  const regular = useMemo(() => presets.filter((p) => !p.is_favorite), [presets]);

  const toggleFavorite = async (preset: Preset) => {
    setBusyId(preset.id);
    try {
      const updated = await presetsApi.setFavorite(preset.id, !preset.is_favorite);
      setPresets((prev) => prev.map((p) => (p.id === preset.id ? updated : p)));
    } finally {
      setBusyId(null);
    }
  };

  if (loading) return <p className="text-center mt-20 text-[var(--text)]">Loading...</p>;
  if (!user) return null;

  return (
    <div className="-mx-4 -my-8 min-h-[calc(100vh-80px)] bg-[#050816] px-4 py-10 text-white sm:px-8">
      <div className="mx-auto max-w-5xl">
        <div className="relative overflow-hidden rounded-[2.25rem] border border-white/10 bg-[linear-gradient(135deg,rgba(12,17,36,0.98),rgba(8,10,20,0.96))] px-6 py-8 shadow-[0_24px_80px_rgba(2,6,23,0.55)] sm:px-10">
          <div className="absolute right-[-8%] top-[-12%] h-72 w-72 rounded-full bg-[radial-gradient(circle,rgba(96,165,250,0.22),rgba(251,146,60,0.16)_45%,transparent_70%)] blur-3xl" />
          <div className="relative z-10 flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
            <div className="max-w-2xl">
              <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.34em] text-orange-200/78">Preset library</p>
              <h1 className="font-['Iowan_Old_Style','Palatino_Linotype','Book_Antiqua','Georgia',serif] text-5xl font-semibold leading-[0.95]">
                Keep your best-ready moods one tap away.
              </h1>
              <p className="mt-4 text-sm leading-7 text-white/65 sm:text-base">
                Favorite the presets you keep coming back to, launch them instantly, or build a new one that feels even more specific.
              </p>
            </div>
            <a href="/discover/create" className="inline-flex rounded-xl border border-orange-300/30 bg-orange-500/15 px-4 py-2.5 text-sm font-semibold text-orange-100 transition hover:border-orange-200/60 hover:bg-orange-500/22 hover:text-white">
              Create a fresh preset
            </a>
          </div>
        </div>

        {favorites.length > 0 && (
          <section className="mt-8 mb-8">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.28em] text-white/46">Pinned favorites</h2>
            <div className="grid gap-4 lg:grid-cols-2">
              {favorites.map((preset) => (
                <PresetCard key={preset.id} preset={preset} onToggleFavorite={toggleFavorite} busy={busyId === preset.id} />
              ))}
            </div>
          </section>
        )}

        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.28em] text-white/46">All presets</h2>
          {regular.length === 0 ? (
            <div className="rounded-[1.75rem] border border-dashed border-white/15 bg-white/[0.04] p-6 text-white/58">
              No extra presets yet. Create one and turn a loose idea into a reusable starting point.
            </div>
          ) : (
            <div className="grid gap-4 lg:grid-cols-2">
              {regular.map((preset) => (
                <PresetCard key={preset.id} preset={preset} onToggleFavorite={toggleFavorite} busy={busyId === preset.id} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
