import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { DarkModeProvider, DarkModeToggle } from "@/lib/dark-mode";
import NavLinks from "./NavLinks";

export const metadata: Metadata = {
  title: "Rowboat",
  description: "AI-powered group outing coordination",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen" style={{ backgroundColor: "var(--bg)", color: "var(--text)" }}>
        <DarkModeProvider>
          <AuthProvider>
            <nav className="border-b px-6 py-3 flex items-center justify-between"
              style={{ backgroundColor: "var(--surface)", borderColor: "var(--border)" }}>
              <a href="/" className="text-xl font-bold text-orange-500">Rowboat</a>
              <div className="flex items-center gap-4 text-sm">
                <NavLinks />
                <DarkModeToggle />
              </div>
            </nav>
            <main className="max-w-2xl mx-auto px-4 py-8">{children}</main>
          </AuthProvider>
        </DarkModeProvider>
      </body>
    </html>
  );
}
