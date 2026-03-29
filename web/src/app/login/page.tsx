"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { auth as authApi } from "@/lib/api";
import { cls } from "@/lib/ui";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await login(email, password);
      router.push("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  };

  const handleGoogle = async () => {
    try {
      const { auth_url } = await authApi.googleUrl();
      window.location.href = auth_url;
    } catch {
      setError("Could not start Google sign-in");
    }
  };

  return (
    <div className="max-w-sm mx-auto mt-16">
      <h1 className="text-2xl font-bold mb-6 text-center text-[var(--text)]">Sign in to Rowboat</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <input type="email" placeholder="Email" value={email}
          onChange={(e) => setEmail(e.target.value)} required className={cls.input} />
        <input type="password" placeholder="Password" value={password}
          onChange={(e) => setPassword(e.target.value)} required className={cls.input} />
        {error && <p className="text-red-500 dark:text-red-400 text-sm">{error}</p>}
        <button type="submit" className={`${cls.btnPrimary} w-full`}>Sign In</button>
      </form>
      <div className="my-4 text-center text-sm" style={{ color: "var(--text-muted)" }}>or</div>
      <button onClick={handleGoogle}
        className={`${cls.btnOutline} w-full`}>
        Continue with Google
      </button>
      <p className="text-center text-sm mt-4" style={{ color: "var(--text-muted)" }}>
        No account?{" "}
        <a href="/register" className="text-orange-600 dark:text-orange-400 font-medium hover:underline">Register</a>
      </p>
    </div>
  );
}
