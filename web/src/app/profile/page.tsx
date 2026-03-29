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
  };

  if (loading || !user) return <p className="text-center mt-20 text-[var(--text)]">Loading...</p>;

  return (
    <div className="max-w-md mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-[var(--text)]">Your Profile</h1>
      <form onSubmit={handleSave} className="flex flex-col gap-4">
        <div>
          <label className={`${cls.label} block mb-1`}>Display Name</label>
          <input value={displayName} onChange={(e) => setDisplayName(e.target.value)}
            placeholder={user.name} className={cls.input} />
        </div>
        <div>
          <label className={`${cls.label} block mb-1`}>Bio</label>
          <textarea value={bio} onChange={(e) => setBio(e.target.value)}
            placeholder="Tell people a bit about yourself..." rows={3} maxLength={500}
            className={cls.textarea} />
        </div>
        <div>
          <label className={`${cls.label} block mb-1`}>Interest Tags (comma-separated)</label>
          <input value={tags} onChange={(e) => setTags(e.target.value)}
            placeholder="e.g. hiking, brunch, live-music" className={cls.input} />
        </div>
        <button type="submit" className={`${cls.btnPrimary} w-full`}>Save Profile</button>
        {saved && <p className="text-green-600 dark:text-green-400 text-sm text-center">Saved!</p>}
      </form>
    </div>
  );
}
