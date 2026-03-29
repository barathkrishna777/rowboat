"use client";

import { useAuth } from "@/lib/auth-context";
import { presets as presetsApi, Preset } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

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

  const builtIn = useMemo(() => presets.filter((p) => p.is_built_in), [presets]);
  const custom = useMemo(() => presets.filter((p) => !p.is_built_in), [presets]);

  const toggleFavorite = async (preset: Preset) => {
    if (preset.is_built_in) return;
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
          <p className="text-[var(--text-muted)]">Curated stacks you can swipe intentionally.</p>
        </div>
        <a href="/discover/create" className="text-sm font-semibold text-orange-500 hover:text-orange-600">+ Create preset</a>
      </div>

      <section className="mb-8">
        <h2 className="text-lg font-semibold text-[var(--text)] mb-3">Built-in presets</h2>
        <div className="grid gap-3">
          {builtIn.map((preset) => (
            <div key={preset.id} className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-5">
              <h3 className="text-lg font-bold text-[var(--text)] mb-1">{preset.name}</h3>
              <p className="text-[var(--text-muted)] mb-3">{preset.description}</p>
              <div className="flex flex-wrap gap-2 mb-4">
                {preset.criteria.vibe.map((chip) => (
                  <span key={chip} className="px-3 py-1 rounded-full text-xs font-semibold bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300">
                    {chip}
                  </span>
                ))}
              </div>
              <a href="/swipe" className="inline-block bg-orange-500 text-white rounded-lg py-2 px-4 font-semibold hover:bg-orange-600">Use this preset</a>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-[var(--text)] mb-3">My custom presets</h2>
        {custom.length === 0 ? (
          <div className="bg-[var(--surface)] border border-dashed border-[var(--border)] rounded-2xl p-5 text-[var(--text-muted)]">
            You haven’t created custom presets yet. Use “Create preset” to add manual presets.
          </div>
        ) : (
          <div className="grid gap-3">
            {custom.map((preset) => (
              <div key={preset.id} className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-lg font-bold text-[var(--text)] mb-1">{preset.name}</h3>
                    <p className="text-[var(--text-muted)]">{preset.description || "No description yet."}</p>
                  </div>
                  <button
                    onClick={() => toggleFavorite(preset)}
                    disabled={busyId === preset.id}
                    className="text-sm font-semibold text-orange-500 hover:text-orange-600 disabled:opacity-50"
                  >
                    {preset.is_favorite ? "★ Favorite" : "☆ Mark favorite"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
