"use client";

import { useAuth } from "@/lib/auth-context";
import { presets as presetsApi } from "@/lib/api";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { criteriaToForm, formToCriteria, PresetEditor } from "../_components/preset-form";

export default function MagicPresetPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  const [prompt, setPrompt] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [cuisines, setCuisines] = useState<string[]>([]);
  const [activities, setActivities] = useState<string[]>([]);
  const [dietary, setDietary] = useState<string[]>([]);
  const [budget, setBudget] = useState("$$");
  const [dealbreakers, setDealbreakers] = useState("");
  const [neighborhoods, setNeighborhoods] = useState("");
  const [accessibility, setAccessibility] = useState("");
  const [parsed, setParsed] = useState(false);
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
      const form = criteriaToForm(result.criteria);
      setCuisines(form.cuisines);
      setActivities(form.activities);
      setDietary(form.dietary);
      setBudget(form.budget);
      setDealbreakers(form.dealbreakers);
      setNeighborhoods(form.neighborhoods);
      setAccessibility(form.accessibility);
      setParsed(true);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to parse prompt");
    } finally {
      setParsing(false);
    }
  };

  const save = async (event: FormEvent) => {
    event.preventDefault();
    if (!parsed || !name.trim()) return;
    setSaving(true);
    try {
      await presetsApi.create({
        name,
        description,
        source: "ai",
        criteria: formToCriteria({
          cuisines,
          activities,
          dietary,
          budget,
          dealbreakers,
          neighborhoods,
          accessibility,
        }),
      });
      router.push("/discover/presets");
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to save preset");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="mt-20 text-center text-[var(--text)]">Loading...</p>;
  if (!user) return null;

  return (
    <div className="mx-auto max-w-6xl px-2 sm:px-4">
      <h1 className="mb-2 text-3xl font-bold text-[var(--text)]">Describe it naturally</h1>
      <p className="mb-6 text-[var(--text-muted)]">
        Let the agent draft the preset, then edit anything before you save it.
      </p>

      <div className="mb-6 border-t border-[var(--border)] pt-6">
        <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]">Your prompt</label>
        <textarea
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          rows={4}
          placeholder="Example: cozy sunday roast with vegetarian options, no loud bars, budget-friendly"
          className="w-full rounded-lg border border-[var(--border)] bg-transparent px-3 py-2"
        />
        <button
          onClick={parse}
          disabled={parsing || !prompt.trim()}
          className="mt-3 rounded-lg bg-orange-500 px-4 py-2 font-semibold text-white hover:bg-orange-600 disabled:opacity-50"
        >
          {parsing ? "Parsing..." : "Generate preset"}
        </button>
      </div>

      {parsed && (
        <form onSubmit={save} className="space-y-5 border-t border-[var(--border)] pt-6">
          <h2 className="text-xl font-bold text-[var(--text)]">Edit before saving</h2>

          <PresetEditor
            name={name}
            description={description}
            onNameChange={setName}
            onDescriptionChange={setDescription}
            cuisines={cuisines}
            activities={activities}
            dietary={dietary}
            budget={budget}
            dealbreakers={dealbreakers}
            neighborhoods={neighborhoods}
            accessibility={accessibility}
            onCuisinesChange={setCuisines}
            onActivitiesChange={setActivities}
            onDietaryChange={setDietary}
            onBudgetChange={setBudget}
            onDealbreakersChange={setDealbreakers}
            onNeighborhoodsChange={setNeighborhoods}
            onAccessibilityChange={setAccessibility}
          />

          <button
            disabled={saving}
            className="rounded-lg bg-orange-500 px-4 py-2 font-semibold text-white hover:bg-orange-600 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save generated preset"}
          </button>
        </form>
      )}
    </div>
  );
}
