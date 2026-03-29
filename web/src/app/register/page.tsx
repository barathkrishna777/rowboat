"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { cls } from "@/lib/ui";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await register(name, email, password);
      router.push("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
    }
  };

  return (
    <div className="max-w-sm mx-auto mt-16">
      <h1 className="text-2xl font-bold mb-6 text-center text-[var(--text)]">Create your account</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
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
        <a href="/login" className="text-orange-600 dark:text-orange-400 font-medium hover:underline">Sign in</a>
      </p>
    </div>
  );
}
