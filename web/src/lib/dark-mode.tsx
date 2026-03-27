"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";

interface DarkModeCtx {
  dark: boolean;
  toggle: () => void;
}

const Ctx = createContext<DarkModeCtx>({ dark: false, toggle: () => {} });

export function DarkModeProvider({ children }: { children: ReactNode }) {
  const [dark, setDark] = useState(false);

  // Initialise from localStorage on mount (avoids SSR mismatch)
  useEffect(() => {
    const stored = localStorage.getItem("dark");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const enabled = stored !== null ? stored === "true" : prefersDark;
    setDark(enabled);
    document.documentElement.classList.toggle("dark", enabled);
  }, []);

  const toggle = () => {
    setDark(prev => {
      const next = !prev;
      localStorage.setItem("dark", String(next));
      document.documentElement.classList.toggle("dark", next);
      return next;
    });
  };

  return <Ctx.Provider value={{ dark, toggle }}>{children}</Ctx.Provider>;
}

export function useDarkMode() {
  return useContext(Ctx);
}

export function DarkModeToggle() {
  const { dark, toggle } = useDarkMode();
  return (
    <button
      onClick={toggle}
      aria-label="Toggle dark mode"
      title={dark ? "Switch to light mode" : "Switch to dark mode"}
      className="w-9 h-9 rounded-lg flex items-center justify-center text-lg
        hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors"
    >
      {dark ? "☀️" : "🌙"}
    </button>
  );
}
