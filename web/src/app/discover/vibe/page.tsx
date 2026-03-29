"use client";

import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function ChooseVibePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading) return <p className="text-center mt-20 text-[var(--text)]">Loading...</p>;
  if (!user) return null;

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-[var(--text)] mb-2">Choose your vibe!</h1>
      <p className="text-[var(--text-muted)] mb-6">
        Phase 1 placeholder: the vibe-first discover flow will be implemented in a later phase.
      </p>
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-6 text-[var(--text-muted)]">
        For now, use presets to swipe intentionally.
      </div>
      <a href="/discover/presets" className="inline-block mt-4 bg-orange-500 text-white rounded-lg py-2 px-4 font-semibold hover:bg-orange-600">
        Go to Presets
      </a>
    </div>
  );
}
