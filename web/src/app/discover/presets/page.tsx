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
    <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-5">
      <div className="flex items-start justify-between gap-3 mb-2">
        <h3 className="text-lg font-bold text-[var(--text)]">{preset.name}</h3>
        <button
          onClick={() => onToggleFavorite(preset)}
          disabled={busy}
          aria-label={preset.is_favorite ? "Unfavorite preset" : "Favorite preset"}
          className={`text-2xl leading-none transition-colors ${preset.is_favorite ? "text-red-500" : "text-[var(--text-muted)] hover:text-red-400"} disabled:opacity-50`}
        >
          ♥
        </button>
      </div>
      <p className="text-[var(--text-muted)] mb-3">{preset.description || "No description yet."}</p>
      <div className="flex flex-wrap gap-2 mb-4">
        {chips.map((chip) => (
          <span key={chip} className="px-3 py-1 rounded-full text-xs font-semibold bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300">
            {chip}
          </span>
        ))}
      </div>
      <a href={`/swipe?preset_id=${encodeURIComponent(preset.id)}`} className="inline-block bg-orange-500 text-white rounded-lg py-2 px-4 font-semibold hover:bg-orange-600">Use this preset</a>
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
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-[var(--text)]">Presets</h1>
          <p className="text-[var(--text-muted)]">Favorite the presets you love and keep them pinned at the top.</p>
        </div>
        <a href="/discover/create" className="text-sm font-semibold text-orange-500 hover:text-orange-600">+ Create preset</a>
      </div>

      {favorites.length > 0 && (
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-[var(--text)] mb-3">Favorite presets</h2>
          <div className="grid gap-3">
            {favorites.map((preset) => (
              <PresetCard key={preset.id} preset={preset} onToggleFavorite={toggleFavorite} busy={busyId === preset.id} />
            ))}
          </div>
        </section>
      )}

      <section>
        <h2 className="text-lg font-semibold text-[var(--text)] mb-3">All presets</h2>
        {regular.length === 0 ? (
          <div className="bg-[var(--surface)] border border-dashed border-[var(--border)] rounded-2xl p-5 text-[var(--text-muted)]">
            No additional presets right now. Create one to get started.
          </div>
        ) : (
          <div className="grid gap-3">
            {regular.map((preset) => (
              <PresetCard key={preset.id} preset={preset} onToggleFavorite={toggleFavorite} busy={busyId === preset.id} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
