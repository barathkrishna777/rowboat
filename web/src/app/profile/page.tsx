"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { profile as profileApi } from "@/lib/api";
import { useRouter } from "next/navigation";
import { cls } from "@/lib/ui";

export default function ProfilePage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [tags, setTags] = useState("");
  const [saved, setSaved] = useState(false);
  const [generatingPrefs, setGeneratingPrefs] = useState(false);
  const [prefsStatus, setPrefsStatus] = useState<"idle" | "done" | "error">("idle");

  useEffect(() => {
    if (!loading && !user) { router.replace("/login"); return; }
    if (user) {
      profileApi.get().then((p) => {
        if (p) {
          setDisplayName(p.display_name || "");
          setBio(p.bio || "");
          setTags((p.interest_tags || []).join(", "));
        }
      }).catch(() => {});
    }
  }, [loading, user, router]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    await profileApi.update({
      display_name: displayName || undefined,
      bio: bio || undefined,
      interest_tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);

    if (bio.trim() || tags.trim()) {
      setGeneratingPrefs(true);
      setPrefsStatus("idle");
      try {
        await profileApi.generatePreferences();
        setPrefsStatus("done");
      } catch {
        setPrefsStatus("error");
      } finally {
        setGeneratingPrefs(false);
        setTimeout(() => setPrefsStatus("idle"), 3000);
      }
    }
  };

  if (loading || !user) return <p className="text-center mt-20">Loading...</p>;

  return (
    <div className="max-w-md mx-auto">
      <h1 className="text-2xl font-bold mb-6">Your Profile</h1>
      <form onSubmit={handleSave} className="flex flex-col gap-4">
        <div>
          <label className={`${cls.label} block mb-1`}>Display Name</label>
          <input value={displayName} onChange={(e) => setDisplayName(e.target.value)}
            placeholder={user.name} className={cls.input} />
        </div>
        <div>
          <label className={`${cls.label} block mb-1`}>Bio</label>
          <textarea value={bio} onChange={(e) => setBio(e.target.value)}
            placeholder="Tell people a bit about yourself — we'll use this to personalize your recommendations..."
            rows={3} maxLength={500}
            className={cls.textarea} />
        </div>
        <div>
          <label className={`${cls.label} block mb-1`}>Interest Tags (comma-separated)</label>
          <input value={tags} onChange={(e) => setTags(e.target.value)}
            placeholder="e.g. hiking, brunch, live-music" className={cls.input} />
        </div>
        <button type="submit" disabled={generatingPrefs} className={`${cls.btnPrimary} w-full`}>
          {generatingPrefs ? "Saving..." : "Save Profile"}
        </button>
        {saved && !generatingPrefs && prefsStatus === "idle" && (
          <p className="text-green-600 dark:text-green-400 text-sm text-center">Saved!</p>
        )}
        {generatingPrefs && (
          <div className="flex items-center justify-center gap-2 text-sm text-orange-600 dark:text-orange-400">
            <span className="inline-block h-4 w-4 border-2 border-orange-300 border-t-orange-600 rounded-full animate-spin" />
            Updating your vibe preferences...
          </div>
        )}
        {prefsStatus === "done" && !generatingPrefs && (
          <p className="text-green-600 dark:text-green-400 text-sm text-center">
            Profile saved and preferences updated!
          </p>
        )}
        {prefsStatus === "error" && !generatingPrefs && (
          <p className="text-amber-600 dark:text-amber-400 text-sm text-center">
            Profile saved, but preference generation failed. Your recommendations may not be personalized.
          </p>
        )}
      </form>
    </div>
  );
}
