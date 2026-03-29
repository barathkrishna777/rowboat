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
      className="group relative overflow-hidden rounded-[2rem] border border-white/12 bg-white/[0.05] p-7 shadow-[0_24px_80px_rgba(7,10,20,0.28)] backdrop-blur-sm transition duration-300 hover:-translate-y-1 hover:border-white/25 hover:bg-white/[0.08]"
    >
      <div className={`absolute inset-0 opacity-80 transition duration-300 group-hover:opacity-100 ${accent}`} />
      <div className="relative z-10">
        <p className="mb-4 text-[11px] font-semibold uppercase tracking-[0.32em] text-white/55">{eyebrow}</p>
        <h2 className="mb-3 max-w-sm font-['Iowan_Old_Style','Palatino_Linotype','Book_Antiqua','Georgia',serif] text-3xl font-semibold leading-[1.02] text-white">
          {title}
        </h2>
        <p className="max-w-md text-sm leading-6 text-white/72">{description}</p>
        <p className="mt-6 text-sm font-semibold text-orange-200 transition group-hover:text-white">Open path</p>
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

  if (loading) return <p className="text-center mt-20 text-[var(--text)]">Loading...</p>;
  if (!user) return null;

  return (
    <div className="-mx-4 -my-8 min-h-[calc(100vh-80px)] overflow-hidden bg-[#050816] px-4 py-10 text-white sm:px-8">
      <div className="mx-auto max-w-5xl">
        <section className="relative overflow-hidden rounded-[2.5rem] border border-white/10 bg-[linear-gradient(135deg,rgba(12,17,36,0.98),rgba(8,10,20,0.96))] px-6 py-10 shadow-[0_24px_80px_rgba(2,6,23,0.55)] sm:px-10 sm:py-14">
          <div className="absolute inset-x-0 top-[-10%] h-64 bg-[radial-gradient(circle_at_top,rgba(96,165,250,0.28),rgba(251,146,60,0.18)_38%,rgba(168,85,247,0.14)_60%,transparent_75%)] blur-3xl" />
          <div className="relative z-10 max-w-3xl">
            <p className="mb-4 text-[11px] font-semibold uppercase tracking-[0.36em] text-orange-200/80">
              Discover
            </p>
            <h1 className="max-w-2xl font-['Iowan_Old_Style','Palatino_Linotype','Book_Antiqua','Georgia',serif] text-5xl font-semibold leading-[0.95] text-white sm:text-6xl">
              Start with a mood or swipe from a preset that already knows your taste.
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-white/68 sm:text-lg">
              The bubble-first experience powers the vibe path. Your preset flows keep the smarter ranking,
              favorites, and creation tools already built into this branch.
            </p>
          </div>

          <section className="relative z-10 mt-10 grid gap-5 lg:grid-cols-2">
            <DiscoveryCard
              eyebrow="Mood-First"
              title="Choose your vibe!"
              description="Pick a few glowing prompts or type your own. We’ll turn that feeling into venue suggestions instantly."
              href="/discover/vibe"
              accent="bg-[radial-gradient(circle_at_top_left,rgba(251,146,60,0.18),transparent_48%),radial-gradient(circle_at_bottom_right,rgba(168,85,247,0.14),transparent_46%)]"
            />
            <DiscoveryCard
              eyebrow="Preset-Driven"
              title="Curated presets, custom taste."
              description="Browse favorites, launch built-ins, or create a sharper preset with natural language when you want more control."
              href="/discover/presets"
              accent="bg-[radial-gradient(circle_at_top_left,rgba(96,165,250,0.2),transparent_48%),radial-gradient(circle_at_bottom_right,rgba(34,197,94,0.12),transparent_44%)]"
            />
          </section>

          <div className="relative z-10 mt-8 flex flex-wrap gap-3 text-xs uppercase tracking-[0.22em] text-white/40">
            <span>Vibe prompts</span>
            <span>Preset favorites</span>
            <span>Natural-language creation</span>
            <span>Intentional swiping</span>
          </div>
        </section>
      </div>
    </div>
  );
}
