"use client";

import { useAuth } from "@/lib/auth-context";
import { Preset, presets as presetsApi } from "@/lib/api";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useEffect, useState } from "react";
import { criteriaToForm, formToCriteria, PresetEditor } from "../_components/preset-form";

function ManualPresetPageInner() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const presetId = searchParams.get("preset_id");

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [cuisines, setCuisines] = useState<string[]>([]);
  const [activities, setActivities] = useState<string[]>([]);
  const [dietary, setDietary] = useState<string[]>([]);
  const [budget, setBudget] = useState("$$");
  const [dealbreakers, setDealbreakers] = useState("");
  const [neighborhoods, setNeighborhoods] = useState("");
  const [accessibility, setAccessibility] = useState("");
  const [saving, setSaving] = useState(false);
  const [loadingPreset, setLoadingPreset] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  useEffect(() => {
    if (!user || !presetId) return;
    setLoadingPreset(true);
    presetsApi.list()
      .then((all) => {
        const preset = all.find((item) => item.id === presetId && !item.is_built_in) as Preset | undefined;
        if (!preset) return;
        setName(preset.name);
        setDescription(preset.description || "");
        const form = criteriaToForm(preset.criteria);
        setCuisines(form.cuisines);
        setActivities(form.activities);
        setDietary(form.dietary);
        setBudget(form.budget);
        setDealbreakers(form.dealbreakers);
        setNeighborhoods(form.neighborhoods);
        setAccessibility(form.accessibility);
      })
      .finally(() => setLoadingPreset(false));
  }, [presetId, user]);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    try {
      const criteria = formToCriteria({
        cuisines,
        activities,
        dietary,
        budget,
        dealbreakers,
        neighborhoods,
        accessibility,
      });

      if (presetId) {
        await presetsApi.update(presetId, {
          name,
          description,
          source: "manual",
          criteria,
        });
      } else {
        await presetsApi.create({
          name,
          description,
          source: "manual",
          criteria,
        });
      }
      router.push("/discover/presets");
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to save preset");
    } finally {
      setSaving(false);
    }
  };

  if (loading || loadingPreset) return <p className="mt-20 text-center text-[var(--text)]">Loading...</p>;
  if (!user) return null;

  return (
    <div className="mx-auto max-w-6xl">
      <h1 className="mb-2 text-3xl font-bold text-[var(--text)]">
        {presetId ? "Edit preset" : "Build preset manually"}
      </h1>
      <p className="mb-6 text-[var(--text-muted)]">
        Shape the preset directly, then save it when it feels right.
      </p>

      <form onSubmit={onSubmit} className="space-y-5 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6">
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
          {saving ? "Saving..." : presetId ? "Save changes" : "Save preset"}
        </button>
      </form>
    </div>
  );
}

export default function ManualPresetPage() {
  return (
    <Suspense fallback={<p className="mt-20 text-center text-[var(--text)]">Loading...</p>}>
      <ManualPresetPageInner />
    </Suspense>
  );
}
