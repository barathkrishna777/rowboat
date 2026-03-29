"use client";

import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

function BigCard({ title, description, href }: { title: string; description: string; href: string }) {
  return (
    <a href={href} className="block bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-8 shadow-sm hover:border-orange-400 transition-colors">
      <h2 className="text-2xl font-bold text-[var(--text)] mb-2">{title}</h2>
      <p className="text-[var(--text-muted)] leading-relaxed">{description}</p>
    </a>
  );
}

export default function DiscoverHomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading) return <p className="text-center mt-20 text-[var(--text)]">Loading...</p>;
  if (!user) return null;

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-[var(--text)] mb-2">Discover</h1>
      <p className="text-[var(--text-muted)] mb-8">Choose how you want to start swiping intentionally.</p>

      <section className="grid gap-4 md:grid-cols-2">
        <BigCard
          title="Choose your vibe!"
          description="Tell us your current mood and we’ll shape discover suggestions around it."
          href="/discover/vibe"
        />
        <BigCard
          title="Presets"
          description="Browse built-in and custom presets, favorite your best ones, and launch a tailored swipe deck."
          href="/discover/presets"
        />
      </section>
    </div>
  );
}
