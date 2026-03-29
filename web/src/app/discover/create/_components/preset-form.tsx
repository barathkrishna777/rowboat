"use client";

import { PresetCriteria } from "@/lib/api";

export const CUISINES = ["Italian", "Japanese", "Mexican", "Indian", "Thai", "American", "Mediterranean", "Korean"];
export const ACTIVITIES = ["Bowling", "Hiking", "Karaoke", "Brunch", "Museum", "Comedy", "Board Games", "Live Music"];
export const DIETARY = ["Vegetarian", "Vegan", "Gluten Free", "Halal", "Kosher", "Dairy Free"];
export const BUDGET_OPTIONS = ["$", "$$", "$$$", "$$$$"];

function Toggle({
  options,
  value,
  onChange,
}: {
  options: string[];
  value: string[];
  onChange: (next: string[]) => void;
}) {
  const toggle = (opt: string) => {
    if (value.includes(opt)) onChange(value.filter((item) => item !== opt));
    else onChange([...value, opt]);
  };

  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => (
        <button
          key={opt}
          type="button"
          onClick={() => toggle(opt)}
          className={`rounded-full border px-3 py-1.5 text-sm font-medium transition-colors ${
            value.includes(opt)
              ? "border-orange-400 bg-orange-50 text-orange-900 dark:bg-orange-950/45 dark:text-orange-100"
              : "border-[var(--border)] text-[var(--text)] hover:border-orange-300"
          }`}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

export function criteriaToForm(criteria: PresetCriteria) {
  return {
    cuisines: criteria.cuisine_preferences.map(capitalizeWords),
    activities: criteria.activity_preferences.map(capitalizeWords),
    dietary: criteria.dietary_restrictions.map((item) => capitalizeWords(item.replace(/_/g, " "))),
    budget: criteria.budget_max || "$$",
    dealbreakers: criteria.dealbreakers.join("\n"),
    neighborhoods: criteria.preferred_neighborhoods.join("\n"),
    accessibility: criteria.accessibility_needs.join("\n"),
  };
}

export function formToCriteria(form: {
  cuisines: string[];
  activities: string[];
  dietary: string[];
  budget: string;
  dealbreakers: string;
  neighborhoods: string;
  accessibility: string;
}): PresetCriteria {
  return {
    cuisine_preferences: form.cuisines.map((item) => item.toLowerCase()),
    activity_preferences: form.activities.map((item) => item.toLowerCase()),
    dietary_restrictions: form.dietary.map((item) => item.toLowerCase().replace(/ /g, "_")),
    budget_max: form.budget,
    dealbreakers: splitLines(form.dealbreakers),
    preferred_neighborhoods: splitLines(form.neighborhoods),
    accessibility_needs: splitLines(form.accessibility),
  };
}

function splitLines(value: string) {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function capitalizeWords(value: string) {
  return value.replace(/\b\w/g, (match) => match.toUpperCase());
}

export function PresetEditor({
  name,
  description,
  onNameChange,
  onDescriptionChange,
  cuisines,
  activities,
  dietary,
  budget,
  dealbreakers,
  neighborhoods,
  accessibility,
  onCuisinesChange,
  onActivitiesChange,
  onDietaryChange,
  onBudgetChange,
  onDealbreakersChange,
  onNeighborhoodsChange,
  onAccessibilityChange,
}: {
  name: string;
  description: string;
  onNameChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
  cuisines: string[];
  activities: string[];
  dietary: string[];
  budget: string;
  dealbreakers: string;
  neighborhoods: string;
  accessibility: string;
  onCuisinesChange: (value: string[]) => void;
  onActivitiesChange: (value: string[]) => void;
  onDietaryChange: (value: string[]) => void;
  onBudgetChange: (value: string) => void;
  onDealbreakersChange: (value: string) => void;
  onNeighborhoodsChange: (value: string) => void;
  onAccessibilityChange: (value: string) => void;
}) {
  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
      <div className="space-y-5">
        <div>
          <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]">Preset name</label>
          <input
            value={name}
            onChange={(event) => onNameChange(event.target.value)}
            required
            className="w-full rounded-lg border border-[var(--border)] bg-transparent px-3 py-2"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]">Description</label>
          <textarea
            value={description}
            onChange={(event) => onDescriptionChange(event.target.value)}
            rows={3}
            className="w-full rounded-lg border border-[var(--border)] bg-transparent px-3 py-2"
          />
        </div>

        <div>
          <p className="mb-2 text-sm font-medium text-[var(--text-muted)]">Budget per person</p>
          <div className="grid grid-cols-2 gap-2">
            {BUDGET_OPTIONS.map((opt) => (
              <button
                key={opt}
                type="button"
                onClick={() => onBudgetChange(opt)}
                className={`rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
                  budget === opt
                    ? "border-orange-400 bg-orange-50 text-orange-900 dark:bg-orange-950/45 dark:text-orange-100"
                    : "border-[var(--border)] text-[var(--text)] hover:border-orange-300"
                }`}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="space-y-5">
        <div>
          <p className="mb-2 text-sm font-medium text-[var(--text-muted)]">Cuisines</p>
          <Toggle options={CUISINES} value={cuisines} onChange={onCuisinesChange} />
        </div>
        <div>
          <p className="mb-2 text-sm font-medium text-[var(--text-muted)]">Activities</p>
          <Toggle options={ACTIVITIES} value={activities} onChange={onActivitiesChange} />
        </div>
        <div>
          <p className="mb-2 text-sm font-medium text-[var(--text-muted)]">Dietary restrictions</p>
          <Toggle options={DIETARY} value={dietary} onChange={onDietaryChange} />
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          <div>
            <p className="mb-1 text-sm font-medium text-[var(--text-muted)]">Dealbreakers</p>
            <textarea
              value={dealbreakers}
              onChange={(event) => onDealbreakersChange(event.target.value)}
              rows={4}
              placeholder={"No loud places\nMust have parking"}
              className="w-full rounded-lg border border-[var(--border)] bg-transparent px-3 py-2"
            />
          </div>
          <div>
            <p className="mb-1 text-sm font-medium text-[var(--text-muted)]">Neighborhoods</p>
            <textarea
              value={neighborhoods}
              onChange={(event) => onNeighborhoodsChange(event.target.value)}
              rows={4}
              placeholder={"Lawrenceville\nShadyside"}
              className="w-full rounded-lg border border-[var(--border)] bg-transparent px-3 py-2"
            />
          </div>
          <div>
            <p className="mb-1 text-sm font-medium text-[var(--text-muted)]">Accessibility</p>
            <textarea
              value={accessibility}
              onChange={(event) => onAccessibilityChange(event.target.value)}
              rows={4}
              placeholder={"Wheelchair access\nQuiet seating"}
              className="w-full rounded-lg border border-[var(--border)] bg-transparent px-3 py-2"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
