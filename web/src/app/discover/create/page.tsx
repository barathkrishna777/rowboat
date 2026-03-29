"use client";

import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

function MethodCard({
  title,
  description,
  href,
  recommended,
}: {
  title: string;
  description: string;
  href: string;
  recommended?: boolean;
}) {
  return (
    <a href={href} className="block border-t border-[var(--border)] py-6 transition-colors hover:border-orange-400">
      {recommended && (
        <p className="text-xs font-semibold uppercase tracking-wide text-orange-500 mb-2">Recommended</p>
      )}
      <h2 className="text-xl font-bold text-[var(--text)] mb-2">{title}</h2>
      <p className="text-[var(--text-muted)]">{description}</p>
    </a>
  );
}

export default function CreatePresetChooserPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading) return <p className="text-center mt-20 text-[var(--text)]">Loading...</p>;
  if (!user) return null;

  return (
    <div className="mx-auto max-w-6xl px-2 sm:px-4">
      <h1 className="text-3xl font-bold text-[var(--text)] mb-2">Create preset</h1>
      <p className="text-[var(--text-muted)] mb-8">
        Choose how you want to build your preset. Both manual and natural-language creation are now available.
      </p>

      <div className="grid gap-0 md:grid-cols-2 md:gap-8">
        <MethodCard
          title="Build manually"
          description="Pick activities, cuisine, and other options one by one."
          href="/discover/create/manual"
        />
        <MethodCard
          title="Describe it naturally"
          description="Type what you want in plain English and let the AI draft a structured preset."
          href="/discover/create/magic"
          recommended
        />
      </div>
    </div>
  );
}
