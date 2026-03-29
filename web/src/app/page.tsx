"use client";

import { useAuth } from "@/lib/auth-context";
import { preferences as prefsApi, UserPreferences } from "@/lib/api";
import { useEffect, useState } from "react";
import { cls } from "@/lib/ui";

// ── Guest landing ─────────────────────────────────────────────────────────────

function GuestLanding() {
  return (
    <div className="text-center mt-16 px-4">
      <h1 className="text-4xl font-bold mb-3 text-[var(--text)]">
        Plan outings with friends,<br />powered by AI
      </h1>
      <p className="text-[var(--text-muted)] mb-10 max-w-md mx-auto text-lg">
        Rowboat coordinates preferences, calendars, and venues — so your group can
        stop deliberating and start going out.
      </p>
      <div className="flex flex-col sm:flex-row gap-3 justify-center max-w-xs mx-auto sm:max-w-none">
        <a href="/register" className={`${cls.btnPrimary} px-8 py-3 text-base`}>
          Create Account
        </a>
        <a href="/login" className={`${cls.btnOutline} px-8 py-3 text-base`}>
          Sign In
        </a>
      </div>

      {/* Feature highlights — easy to edit copy here */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-16 text-left max-w-2xl mx-auto">
        {[
          { icon: "🤖", title: "AI-powered search", body: "Finds venues across Google Places, Yelp, and more." },
          { icon: "📅", title: "Calendar coordination", body: "Finds times that actually work for everyone." },
          { icon: "✨", title: "Ranked recommendations", body: "Scores venues against your group's real preferences." },
        ].map((f) => (
          <div key={f.title} className={`${cls.card} p-5`}>
            <div className="text-2xl mb-2">{f.icon}</div>
            <div className="font-semibold mb-1 text-[var(--text)]">{f.title}</div>
            <div className="text-sm text-[var(--text-muted)]">{f.body}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Preference summary section ────────────────────────────────────────────────

function PreferenceSection({ userId }: { userId: string }) {
  const [prefs, setPrefs] = useState<UserPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [empty, setEmpty] = useState(false);

  useEffect(() => {
    prefsApi.get(userId)
      .then(setPrefs)
      .catch(() => setEmpty(true))
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) return <p className="text-sm text-[var(--text-muted)]">Loading preferences…</p>;

  if (empty || !prefs) {
    return (
      <div className={`${cls.card} p-5 mt-6`}>
        <h2 className="font-semibold text-[var(--text)] mb-1">Your Preferences</h2>
        <p className="text-sm text-[var(--text-muted)] mb-3">
          You haven&apos;t set your preferences yet. Setting them helps Rowboat rank venues for your group.
        </p>
        {/* TODO: link to /preferences once that page exists */}
        <a href="/profile" className="text-orange-500 hover:text-orange-600 text-sm font-semibold">
          Set preferences →
        </a>
      </div>
    );
  }

  const hasCuisines = prefs.cuisine_preferences?.length > 0;
  const hasActivities = prefs.activity_preferences?.length > 0;
  const hasDietary = prefs.dietary_restrictions?.length > 0;

  return (
    <div className={`${cls.card} p-5 mt-6`}>
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-[var(--text)]">Your Preferences</h2>
        {/* Easy to swap this link once a /preferences page exists */}
        <a href="/profile" className="text-xs text-orange-500 hover:text-orange-600 font-medium">
          Edit
        </a>
      </div>

      <div className="flex flex-col gap-3">
        {/* Budget */}
        {prefs.budget_max && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-[var(--text-muted)] w-24 shrink-0">Budget</span>
            <span className="bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300 font-semibold px-2 py-0.5 rounded">
              {prefs.budget_max}
            </span>
          </div>
        )}

        {/* Cuisines */}
        {hasCuisines && (
          <div className="flex items-start gap-2 text-sm">
            <span className="text-[var(--text-muted)] w-24 shrink-0 pt-0.5">Cuisines</span>
            <div className="flex flex-wrap gap-1.5">
              {prefs.cuisine_preferences.map((c) => (
                <span key={c} className="bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] text-xs px-2 py-0.5 rounded-full">
                  {c}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Activities */}
        {hasActivities && (
          <div className="flex items-start gap-2 text-sm">
            <span className="text-[var(--text-muted)] w-24 shrink-0 pt-0.5">Activities</span>
            <div className="flex flex-wrap gap-1.5">
              {prefs.activity_preferences.map((a) => (
                <span key={a} className="bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] text-xs px-2 py-0.5 rounded-full">
                  {a}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Dietary */}
        {hasDietary && (
          <div className="flex items-start gap-2 text-sm">
            <span className="text-[var(--text-muted)] w-24 shrink-0 pt-0.5">Dietary</span>
            <div className="flex flex-wrap gap-1.5">
              {prefs.dietary_restrictions.map((d) => (
                <span key={d} className="bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] text-xs px-2 py-0.5 rounded-full">
                  {d}
                </span>
              ))}
            </div>
          </div>
        )}

        {!hasCuisines && !hasActivities && !hasDietary && (
          <p className="text-sm text-[var(--text-muted)]">
            Preferences saved but no details yet.{" "}
            <a href="/profile" className="text-orange-500 hover:text-orange-600 font-medium">Fill them in →</a>
          </p>
        )}
      </div>
    </div>
  );
}

// ── Authenticated home ────────────────────────────────────────────────────────

function AuthenticatedHome({ userName, userId }: { userName: string; userId: string }) {
  return (
    <div className="mt-8">
      <h1 className="text-3xl font-bold mb-1 text-[var(--text)]">Welcome back, {userName}!</h1>
      <p className="text-[var(--text-muted)] mb-6">What would you like to do?</p>

      {/* Action buttons — easy to reorder or add/remove */}
      <div className="flex flex-col gap-3 max-w-xs">
        <a href="/plan" className={`${cls.btnPrimary} py-3 px-6 text-center`}>
          🗓 Plan an Outing
        </a>
        <a href="/swipe" className={`${cls.btnOutline} py-3 px-6 text-center`}>
          ✨ Discover Hangouts
        </a>
        <a href="/friends" className={`${cls.btnOutline} py-3 px-6 text-center`}>
          👥 Friends
        </a>
        <a href="/profile" className={`${cls.btnOutline} py-3 px-6 text-center`}>
          ✏️ Edit Profile
        </a>
      </div>

      {/* Preference summary — fetches live data, shows placeholder if not set */}
      <PreferenceSection userId={userId} />
    </div>
  );
}

// ── Page entry point ──────────────────────────────────────────────────────────

export default function HomePage() {
  const { user, loading } = useAuth();

  // Show nothing during the auth hydration tick to avoid flash
  if (loading) return <p className="text-center mt-20 text-[var(--text)]">Loading…</p>;

  // Unauthenticated: show landing page (no redirect)
  if (!user) return <GuestLanding />;

  // Authenticated: show personalised home
  return <AuthenticatedHome userName={user.name} userId={user.id} />;
}
