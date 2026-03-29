"use client";

import { useAuth } from "@/lib/auth-context";
import { presets as presetsApi } from "@/lib/api";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

const CUISINES = ["Italian", "Japanese", "Mexican", "Indian", "Thai", "American", "Mediterranean", "Korean"];
const ACTIVITIES = ["Bowling", "Hiking", "Karaoke", "Brunch", "Museum", "Comedy", "Board Games", "Live Music"];
const DIETARY = ["Vegetarian", "Vegan", "Gluten Free", "Halal", "Kosher", "Dairy Free"];
const BUDGET_OPTIONS = ["$", "$$", "$$$", "$$$$"];

function Toggle({ options, value, onChange }: { options: string[]; value: string[]; onChange: (v: string[]) => void }) {
  const toggle = (opt: string) => {
    if (value.includes(opt)) onChange(value.filter((v) => v !== opt));
    else onChange([...value, opt]);
  };
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => (
        <button
          key={opt}
          type="button"
          onClick={() => toggle(opt)}
          className={`px-3 py-1.5 rounded-full text-sm border font-medium transition-colors ${value.includes(opt)
            ? "border-orange-400 bg-orange-50 text-orange-900 dark:bg-orange-950/45 dark:text-orange-100"
            : "border-[var(--border)] text-[var(--text)] hover:border-orange-300"}`}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

export default function ManualPresetPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [cuisines, setCuisines] = useState<string[]>([]);
  const [activities, setActivities] = useState<string[]>([]);
  const [dietary, setDietary] = useState<string[]>([]);
  const [budget, setBudget] = useState("$$");
  const [dealbreakers, setDealbreakers] = useState("");
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
          cuisine_preferences: cuisines.map((c) => c.toLowerCase()),
          activity_preferences: activities.map((a) => a.toLowerCase()),
          dietary_restrictions: dietary.map((d) => d.toLowerCase().replace(/ /g, "_")),
          budget_max: budget,
          dealbreakers: dealbreakers.split("\n").map((d) => d.trim()).filter(Boolean),
          preferred_neighborhoods: [],
          accessibility_needs: [],
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
      <p className="text-[var(--text-muted)] mb-6">Set cuisines, activities, dietary preferences, budget, and dealbreakers - just like outing preferences.</p>

      <form onSubmit={onSubmit} className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">Preset name</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required className="w-full border border-[var(--border)] rounded-lg px-3 py-2 bg-transparent" />
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-muted)] mb-1">Description</label>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} className="w-full border border-[var(--border)] rounded-lg px-3 py-2 bg-transparent" />
        </div>

        <div>
          <p className="text-sm font-medium text-[var(--text-muted)] mb-2">Cuisines</p>
          <Toggle options={CUISINES} value={cuisines} onChange={setCuisines} />
        </div>
        <div>
          <p className="text-sm font-medium text-[var(--text-muted)] mb-2">Activities</p>
          <Toggle options={ACTIVITIES} value={activities} onChange={setActivities} />
        </div>
        <div>
          <p className="text-sm font-medium text-[var(--text-muted)] mb-2">Dietary restrictions</p>
          <Toggle options={DIETARY} value={dietary} onChange={setDietary} />
        </div>

        <div>
          <p className="text-sm font-medium text-[var(--text-muted)] mb-2">Budget per person</p>
          <div className="grid grid-cols-2 gap-2">
            {BUDGET_OPTIONS.map((opt) => (
              <button
                key={opt}
                type="button"
                onClick={() => setBudget(opt)}
                className={`py-2 px-3 rounded-lg border text-sm font-medium transition-colors ${budget === opt
                  ? "border-orange-400 bg-orange-50 text-orange-900 dark:bg-orange-950/45 dark:text-orange-100"
                  : "border-[var(--border)] text-[var(--text)] hover:border-orange-300"}`}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="text-sm font-medium text-[var(--text-muted)] mb-1">Dealbreakers (one per line)</p>
          <textarea
            value={dealbreakers}
            onChange={(e) => setDealbreakers(e.target.value)}
            rows={3}
            placeholder={"No loud places\nMust have parking"}
            className="w-full border border-[var(--border)] rounded-lg px-3 py-2 bg-transparent"
          />
        </div>

        <button disabled={saving} className="bg-orange-500 text-white rounded-lg px-4 py-2 font-semibold hover:bg-orange-600 disabled:opacity-50">
          {saving ? "Saving..." : "Save preset"}
        </button>
      </form>
    </div>
  );
}
