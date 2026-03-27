"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { auth as authApi } from "@/lib/api";

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
      <h1 className="text-2xl font-bold mb-6 text-center">Sign in to Rowboat</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <input
          type="email" placeholder="Email" value={email}
          onChange={(e) => setEmail(e.target.value)} required
          className="border border-gray-300 rounded-lg px-4 py-2 focus:outline-orange-500"
        />
        <input
          type="password" placeholder="Password" value={password}
          onChange={(e) => setPassword(e.target.value)} required
          className="border border-gray-300 rounded-lg px-4 py-2 focus:outline-orange-500"
        />
        {error && <p className="text-red-500 text-sm">{error}</p>}
        <button type="submit" className="bg-orange-500 text-white rounded-lg py-2 font-semibold hover:bg-orange-600">
          Sign In
        </button>
      </form>
      <div className="my-4 text-center text-gray-400 text-sm">or</div>
      <button
        onClick={handleGoogle}
        className="w-full border border-gray-300 rounded-lg py-2 font-semibold hover:border-orange-400"
      >
        Continue with Google
      </button>
      <p className="text-center text-sm mt-4 text-gray-500">
        No account? <a href="/register" className="text-orange-500 font-medium">Register</a>
      </p>
    </div>
  );
}
