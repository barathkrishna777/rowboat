"use client";

import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

function DiscoveryCard({
  eyebrow,
  title,
  description,
  href,
  accent,
}: {
  eyebrow: string;
  title: string;
  description: string;
  href: string;
  accent: string;
}) {
  return (
    <a
      href={href}
      className="group rounded-[1.75rem] border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[0_12px_40px_rgba(15,23,42,0.08)] transition hover:-translate-y-0.5 hover:border-orange-300 dark:shadow-[0_18px_60px_rgba(2,6,23,0.35)] dark:hover:border-orange-500/40"
    >
      <div className="flex h-full flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start gap-4">
          <div className={`h-12 w-1.5 rounded-full ${accent}`} />
          <div>
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.26em] text-[var(--text-muted)]">
              {eyebrow}
            </p>
            <h2 className="font-['Iowan_Old_Style','Palatino_Linotype','Book_Antiqua','Georgia',serif] text-3xl font-semibold leading-tight text-[var(--text)]">
              {title}
            </h2>
            <p className="mt-2 max-w-md text-sm leading-6 text-[var(--text-muted)]">{description}</p>
          </div>
        </div>
        <div className="inline-flex w-fit rounded-full border border-orange-200 bg-orange-50 px-4 py-2 text-sm font-semibold text-orange-700 transition group-hover:border-orange-300 group-hover:bg-orange-100 dark:border-orange-500/25 dark:bg-orange-500/10 dark:text-orange-200 dark:group-hover:border-orange-400/45 dark:group-hover:bg-orange-500/16">
          Open
        </div>
      </div>
    </a>
  );
}

export default function DiscoverHomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading) return <p className="mt-20 text-center text-[var(--text)]">Loading...</p>;
  if (!user) return null;

  return (
    <div className="-mx-4 -my-8 px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <section className="relative overflow-hidden rounded-[2rem] border border-[var(--border)] bg-[var(--surface)] px-5 py-6 shadow-[0_14px_48px_rgba(15,23,42,0.08)] dark:shadow-[0_22px_72px_rgba(2,6,23,0.35)] sm:px-8">
          <div className="absolute inset-x-0 top-0 h-40 bg-gradient-to-r from-orange-200/45 via-sky-100/55 to-emerald-100/35 blur-3xl dark:from-orange-500/12 dark:via-sky-500/10 dark:to-emerald-500/8" />

          <div className="relative grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.4fr)] lg:items-start">
            <div className="max-w-md">
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.32em] text-[var(--text-muted)]">
                Discover
              </p>
              <h1 className="font-['Iowan_Old_Style','Palatino_Linotype','Book_Antiqua','Georgia',serif] text-5xl font-semibold leading-[0.94] text-[var(--text)]">
                Pick a starting point.
              </h1>
              <p className="mt-3 text-sm leading-6 text-[var(--text-muted)]">
                Mood-first when you want speed. Presets when you want precision.
              </p>
            </div>

            <div className="grid gap-4">
              <DiscoveryCard
                eyebrow="Mood-first"
                title="Choose your vibe"
                description="Quick prompts and custom keywords for fast discovery."
                href="/discover/vibe"
                accent="bg-gradient-to-b from-orange-400 via-pink-400 to-violet-500"
              />
              <DiscoveryCard
                eyebrow="Preset-driven"
                title="Browse presets"
                description="Launch favorites or create a sharper preset when you want control."
                href="/discover/presets"
                accent="bg-gradient-to-b from-sky-400 via-cyan-400 to-emerald-500"
              />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
