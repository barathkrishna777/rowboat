"use client";

import { useAuth } from "@/lib/auth-context";
import { presets as presetsApi, Preset } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

function BigCard({
  title,
  description,
  href,
  badge,
}: {
  title: string;
  description: string;
  href?: string;
  badge?: string;
}) {
  const content = (
    <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-6 shadow-sm hover:border-orange-400 transition-colors">
      {badge && (
        <p className="text-xs font-semibold uppercase tracking-wide text-orange-500 mb-2">
          {badge}
        </p>
      )}
      <h2 className="text-xl font-bold text-[var(--text)] mb-2">{title}</h2>
      <p className="text-[var(--text-muted)] leading-relaxed">{description}</p>
    </div>
  );

  if (!href) return content;
  return <a href={href} className="block">{content}</a>;
}

export default function DiscoverHomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [presets, setPresets] = useState<Preset[]>([]);

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  useEffect(() => {
    if (!user) return;
    presetsApi.list().then(setPresets).catch(() => setPresets([]));
  }, [user]);

  const favoriteCards = useMemo(() => {
    const favorites = presets.filter((p) => p.is_favorite).slice(0, 4);
    if (favorites.length > 0) return favorites;
    return presets.slice(0, 4);
  }, [presets]);

  if (loading) return <p className="text-center mt-20 text-[var(--text)]">Loading...</p>;
  if (!user) return null;

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-[var(--text)] mb-2">Discover</h1>
      <p className="text-[var(--text-muted)] mb-8">
        Swipe intentionally by choosing a vibe or starting with curated presets.
      </p>

      <section className="grid gap-4 md:grid-cols-2 mb-10">
        <BigCard
          title="Choose your vibe!"
          description="Tell us your mood and we’ll shape your discover deck around it."
          href="/discover/vibe"
          badge="Intentional swipe"
        />
        <BigCard
          title="Presets"
          description="Jump into high-quality preset stacks like party nights, hikes, and food plans."
          href="/discover/presets"
          badge="Implemented in this branch"
        />
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-semibold text-[var(--text)] mb-3">Your favorite preset cards</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          {favoriteCards.map((preset) => (
            <BigCard key={preset.id} title={preset.name} description={preset.description || "Saved discover preset."} />
          ))}
          {favoriteCards.length === 0 && (
            <BigCard title="No favorites yet" description="Mark custom presets as favorites to pin them here." />
          )}
        </div>
      </section>

      <section>
        <a
          href="/discover/create"
          className="block bg-orange-500 text-white rounded-2xl p-6 shadow-sm hover:bg-orange-600 transition-colors"
        >
          <p className="text-xs font-semibold uppercase tracking-wide mb-2">Create preset</p>
          <h2 className="text-xl font-bold mb-2">Build your own discover formula</h2>
          <p className="text-orange-100 leading-relaxed">
            Create presets manually or describe them naturally and let the AI assistant draft them for you.
          </p>
        </a>
      </section>
    </div>
  );
}
