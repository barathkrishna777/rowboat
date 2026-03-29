"use client";

import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function ManualPresetPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading) return <p className="text-center mt-20 text-[var(--text)]">Loading...</p>;
  if (!user) return null;

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-[var(--text)] mb-2">Build preset manually</h1>
      <p className="text-[var(--text-muted)] mb-6">
        Phase 1 scaffold: this page is ready for the manual preset form in the next phase.
      </p>
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-6 text-[var(--text-muted)]">
        Coming next: activity, cuisine, budget, and filter pickers.
      </div>
    </div>
  );
}
