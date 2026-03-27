/**
 * Reusable Tailwind class strings for consistent dark-mode-aware styling.
 * Import these instead of repeating long class lists in every page.
 */

export const cls = {
  // Page-level card / panel
  card: "bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl",

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

  btnOutline: "border border-gray-300 dark:border-slate-600 rounded-lg py-2.5 px-4 " +
    "text-gray-600 dark:text-slate-300 font-semibold " +
    "hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors",

  // Labels
  label: "text-sm font-medium text-gray-600 dark:text-slate-400",

  // Muted text
  muted: "text-gray-500 dark:text-slate-400",

  // Divider
  divider: "border-t border-gray-200 dark:border-slate-700",
} as const;
