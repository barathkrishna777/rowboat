"use client";

import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { DarkModeToggle } from "@/lib/dark-mode";

export function NavBar() {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleSignOut = () => {
    logout();
    router.push("/login");
  };

  return (
    <nav
      className="border-b px-6 py-3 flex items-center justify-between"
      style={{ backgroundColor: "var(--surface)", borderColor: "var(--border)" }}
    >
      <a href="/" className="text-xl font-bold text-orange-500">Rowboat</a>
      <div className="flex items-center gap-4 text-sm">
        {user ? (
          <>
            <a href="/plan" className="font-semibold hover:text-orange-500">Plan Outing</a>
            <a href="/swipe" className="hover:text-orange-500">Discover</a>
            <a href="/friends" className="hover:text-orange-500">Friends</a>
            <a href="/profile" className="hover:text-orange-500">Profile</a>
            <button
              onClick={handleSignOut}
              className="text-red-400 hover:text-red-500 font-medium transition-colors"
            >
              Sign Out
            </button>
          </>
        ) : (
          <a href="/login" className="text-orange-500 font-medium hover:text-orange-600">Sign In</a>
        )}
        <DarkModeToggle />
      </div>
    </nav>
  );
}
