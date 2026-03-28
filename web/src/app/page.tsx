"use client";

import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading) return <p className="text-center mt-20">Loading...</p>;
  if (!user) return null;

  return (
    <div className="text-center mt-12">
      <h1 className="text-3xl font-bold mb-2">Welcome back, {user.name}!</h1>
      <p className="text-gray-500 mb-8">What would you like to do?</p>
      <div className="flex flex-col gap-3 max-w-xs mx-auto">
        <a href="/plan" className="bg-orange-500 text-white rounded-lg py-3 px-6 font-semibold hover:bg-orange-600 text-center">
          🗓 Plan an Outing
        </a>
        <a href="/swipe" className="bg-white dark:bg-slate-800 border border-gray-300 dark:border-slate-600 text-gray-700 dark:text-slate-100 rounded-lg py-3 px-6 font-semibold hover:border-orange-400 dark:hover:border-orange-400 text-center">
          ✨ Discover Hangouts
        </a>
        <a href="/friends" className="bg-white dark:bg-slate-800 border border-gray-300 dark:border-slate-600 text-gray-700 dark:text-slate-100 rounded-lg py-3 px-6 font-semibold hover:border-orange-400 dark:hover:border-orange-400 text-center">
          👥 Friends
        </a>
        <a href="/profile" className="bg-white dark:bg-slate-800 border border-gray-300 dark:border-slate-600 text-gray-700 dark:text-slate-100 rounded-lg py-3 px-6 font-semibold hover:border-orange-400 dark:hover:border-orange-400 text-center">
          ✏️ Edit Profile
        </a>
      </div>
    </div>
  );
}
