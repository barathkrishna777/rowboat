/**
 * Reusable Tailwind class strings for consistent dark-mode-aware styling.
 * Import these instead of repeating long class lists in every page.
 */

export const cls = {
  // Page-level card / panel (tokens keep surface + text in sync in dark mode)
  card: "bg-[var(--surface)] border border-[var(--border)] rounded-xl text-[var(--text)]",

  // Form inputs
  input: "w-full border border-gray-300 dark:border-slate-600 rounded-lg px-4 py-2.5 text-sm " +
    "bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100 " +
    "placeholder:text-gray-400 dark:placeholder:text-slate-500 " +
    "focus:outline-none focus:ring-2 focus:ring-orange-400",

  textarea: "w-full border border-gray-300 dark:border-slate-600 rounded-lg px-4 py-2.5 text-sm " +
    "bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100 " +
    "placeholder:text-gray-400 dark:placeholder:text-slate-500 " +
    "focus:outline-none focus:ring-2 focus:ring-orange-400",

  // Buttons
  btnPrimary: "bg-orange-500 text-white rounded-lg py-2.5 px-4 font-semibold " +
    "hover:bg-orange-600 disabled:opacity-50 transition-colors",

  btnOutline: "border border-[var(--border)] rounded-lg py-2.5 px-4 " +
    "text-[var(--text)] font-semibold " +
    "hover:bg-black/5 dark:hover:bg-white/10 transition-colors",

  // Labels
  label: "text-sm font-medium text-[var(--text-muted)]",

  // Muted text
  muted: "text-[var(--text-muted)]",

  // Divider
  divider: "border-t border-[var(--border)]",
} as const;
