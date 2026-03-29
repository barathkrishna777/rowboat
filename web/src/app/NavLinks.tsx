"use client";

import { useAuth } from "@/lib/auth-context";

export default function NavLinks() {
  const { user, logout } = useAuth();

  if (!user) {
    return (
      <>
        <a href="/login" className="hover:text-orange-500">Sign In</a>
        <a href="/register" className="bg-orange-500 text-white rounded-lg px-3 py-1.5 font-semibold hover:bg-orange-600">
          Sign Up
        </a>
      </>
    );
  }

  return (
    <>
      <a href="/plan" className="font-semibold hover:text-orange-500">Plan Outing</a>
      <a href="/swipe" className="hover:text-orange-500">Discover</a>
      <a href="/friends" className="hover:text-orange-500">Friends</a>
      <a href="/profile" className="hover:text-orange-500">Profile</a>
      <button onClick={logout} className="hover:text-orange-500 text-[var(--text-muted)]">
        Sign Out
      </button>
    </>
  );
}
