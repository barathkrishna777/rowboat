"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { profile as profileApi } from "@/lib/api";
import { useRouter } from "next/navigation";
import { cls } from "@/lib/ui";

type Step = "credentials" | "bio";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();

  const [step, setStep] = useState<Step>("credentials");

  // Step 1 — credentials
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  // Step 2 — bio & tags
  const [bio, setBio] = useState("");
  const [tags, setTags] = useState("");
  const [generating, setGenerating] = useState(false);
  const [prefsDone, setPrefsDone] = useState(false);

  const handleCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await register(name, email, password);
      setStep("bio");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
    }
  };

  const handleSaveBio = async () => {
    if (!bio.trim() && !tags.trim()) {
      router.push("/");
      return;
    }
    setError("");
    setGenerating(true);
    try {
      await profileApi.update({
        display_name: name || undefined,
        bio: bio || undefined,
        interest_tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
      });
      await profileApi.generatePreferences();
      setPrefsDone(true);
      setTimeout(() => router.push("/"), 1200);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save profile");
      setGenerating(false);
    }
  };

  // ── Step 1: Credentials ────────────────────────────────────────────

  if (step === "credentials") {
    return (
      <div className="max-w-sm mx-auto mt-16">
        <h1 className="text-2xl font-bold mb-6 text-center">Create your account</h1>
        <form onSubmit={handleCredentials} className="flex flex-col gap-4">
          <input type="text" placeholder="Full name" value={name}
            onChange={(e) => setName(e.target.value)} required className={cls.input} />
          <input type="email" placeholder="Email" value={email}
            onChange={(e) => setEmail(e.target.value)} required className={cls.input} />
          <input type="password" placeholder="Password" value={password}
            onChange={(e) => setPassword(e.target.value)} required minLength={6} className={cls.input} />
          {error && <p className="text-red-500 dark:text-red-400 text-sm">{error}</p>}
          <button type="submit" className={`${cls.btnPrimary} w-full`}>Create Account</button>
        </form>
        <p className="text-center text-sm mt-4" style={{ color: "var(--text-muted)" }}>
          Already have an account?{" "}
          <a href="/login" className="text-orange-500 font-medium">Sign in</a>
        </p>
      </div>
    );
  }

  // ── Step 2: Bio & interests ────────────────────────────────────────

  return (
    <div className="max-w-sm mx-auto mt-16">
      <h1 className="text-2xl font-bold mb-2 text-center">Tell us about yourself</h1>
      <p className={`text-center text-sm mb-6 ${cls.muted}`}>
        We&apos;ll use this to personalize your hangout recommendations.
      </p>

      <div className="flex flex-col gap-4">
        <div>
          <label className={`${cls.label} block mb-1`}>Short bio</label>
          <textarea
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            placeholder="I love craft beer, bowling nights, and trying new ramen spots. Weekends are for hiking or brunch with friends."
            rows={4}
            maxLength={500}
            className={cls.textarea}
            disabled={generating}
          />
        </div>

        <div>
          <label className={`${cls.label} block mb-1`}>Interest tags (comma-separated)</label>
          <input
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="e.g. hiking, brunch, live-music, karaoke"
            className={cls.input}
            disabled={generating}
          />
        </div>

        {error && <p className="text-red-500 dark:text-red-400 text-sm">{error}</p>}

        {prefsDone ? (
          <div className="text-center py-3">
            <p className="text-green-600 dark:text-green-400 font-semibold">Preferences saved! Redirecting...</p>
          </div>
        ) : (
          <>
            <button
              onClick={handleSaveBio}
              disabled={generating}
              className={`${cls.btnPrimary} w-full flex items-center justify-center gap-2`}
            >
              {generating ? (
                <>
                  <span className="inline-block h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Generating your vibe profile...
                </>
              ) : (
                "Save & Continue"
              )}
            </button>

            <button
              onClick={() => router.push("/")}
              disabled={generating}
              className="text-sm text-center text-orange-500 hover:text-orange-600 font-medium"
            >
              Skip for now
            </button>
          </>
        )}
      </div>
    </div>
  );
}
