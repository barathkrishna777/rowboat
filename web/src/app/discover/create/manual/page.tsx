"use client";

import { useAuth } from "@/lib/auth-context";
import { presets as presetsApi } from "@/lib/api";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

function toList(v: string) {
  return v
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

export default function ManualPresetPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [activities, setActivities] = useState("");
  const [cuisines, setCuisines] = useState("");
  const [vibe, setVibe] = useState("");
  const [budget, setBudget] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    try {
      await presetsApi.create({
        name,
        description,
        source: "manual",
        criteria: {
          activities: toList(activities),
          cuisines: toList(cuisines),
          vibe: toList(vibe),
          budget: budget || undefined,
        },
      });
      router.push("/discover/presets");
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to save preset");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="text-center mt-20 text-[var(--text)]">Loading...</p>;
  if (!user) return null;

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-[var(--text)] mb-2">Build preset manually</h1>
      <p className="text-[var(--text-muted)] mb-6">Create a reusable discover preset by setting your preferred filters.</p>

      <form onSubmit={onSubmit} className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">Preset name</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required className="w-full border border-[var(--border)] rounded-lg p-2 bg-transparent" />
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">Description</label>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} className="w-full border border-[var(--border)] rounded-lg p-2 bg-transparent" />
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">Activities (comma-separated)</label>
            <input value={activities} onChange={(e) => setActivities(e.target.value)} className="w-full border border-[var(--border)] rounded-lg p-2 bg-transparent" />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">Cuisines (comma-separated)</label>
            <input value={cuisines} onChange={(e) => setCuisines(e.target.value)} className="w-full border border-[var(--border)] rounded-lg p-2 bg-transparent" />
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">Vibe tags (comma-separated)</label>
            <input value={vibe} onChange={(e) => setVibe(e.target.value)} className="w-full border border-[var(--border)] rounded-lg p-2 bg-transparent" />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">Budget</label>
            <input value={budget} onChange={(e) => setBudget(e.target.value)} placeholder="$, $$, $$$" className="w-full border border-[var(--border)] rounded-lg p-2 bg-transparent" />
          </div>
        </div>

        <button disabled={saving} className="bg-orange-500 text-white rounded-lg px-4 py-2 font-semibold hover:bg-orange-600 disabled:opacity-50">
          {saving ? "Saving..." : "Save preset"}
        </button>
      </form>
    </div>
  );
}
