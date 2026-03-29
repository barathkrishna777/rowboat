"use client";

import { useAuth } from "@/lib/auth-context";
import { presets as presetsApi, PresetCriteria } from "@/lib/api";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

export default function MagicPresetPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  const [prompt, setPrompt] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [criteria, setCriteria] = useState<PresetCriteria | null>(null);
  const [parsing, setParsing] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  const parse = async () => {
    if (!prompt.trim()) return;
    setParsing(true);
    try {
      const result = await presetsApi.parse(prompt);
      setName(result.name_suggestion || "Custom preset");
      setDescription(result.description_suggestion || "Generated from your description");
      setCriteria(result.criteria);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to parse prompt");
    } finally {
      setParsing(false);
    }
  };

  const save = async (e: FormEvent) => {
    e.preventDefault();
    if (!criteria || !name.trim()) return;
    setSaving(true);
    try {
      await presetsApi.create({
        name,
        description,
        source: "ai",
        criteria,
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
      <h1 className="text-3xl font-bold text-[var(--text)] mb-2">Describe it naturally</h1>
      <p className="text-[var(--text-muted)] mb-6">
        Describe your ideal outing preset. We’ll parse it into structured filters you can save.
      </p>

      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-6 mb-6">
        <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">Your prompt</label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={4}
          placeholder="Example: cozy sunday roast with vegetarian options, no loud bars, budget-friendly"
          className="w-full border border-[var(--border)] rounded-lg px-3 py-2 bg-transparent"
        />
        <button onClick={parse} disabled={parsing || !prompt.trim()} className="mt-3 bg-orange-500 text-white rounded-lg px-4 py-2 font-semibold hover:bg-orange-600 disabled:opacity-50">
          {parsing ? "Parsing..." : "Generate preset"}
        </button>
      </div>

      {criteria && (
        <form onSubmit={save} className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-6 space-y-4">
          <h2 className="text-xl font-bold text-[var(--text)]">Review and save</h2>

          <div>
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">Preset name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} className="w-full border border-[var(--border)] rounded-lg px-3 py-2 bg-transparent" required />
          </div>

          <div>
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">Description</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} className="w-full border border-[var(--border)] rounded-lg px-3 py-2 bg-transparent" />
          </div>

          <div className="text-sm text-[var(--text-muted)] space-y-1">
            <p><strong>Activities:</strong> {criteria.activity_preferences.join(", ") || "—"}</p>
            <p><strong>Cuisines:</strong> {criteria.cuisine_preferences.join(", ") || "—"}</p>
            <p><strong>Dietary:</strong> {criteria.dietary_restrictions.join(", ") || "—"}</p>
            <p><strong>Budget:</strong> {criteria.budget_max || "—"}</p>
            <p><strong>Dealbreakers:</strong> {criteria.dealbreakers.join(", ") || "—"}</p>
          </div>

          <button disabled={saving} className="bg-orange-500 text-white rounded-lg px-4 py-2 font-semibold hover:bg-orange-600 disabled:opacity-50">
            {saving ? "Saving..." : "Save generated preset"}
          </button>
        </form>
      )}
    </div>
  );
}
