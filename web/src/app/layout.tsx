import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { DarkModeProvider } from "@/lib/dark-mode";
import { NavBar } from "./navbar";

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
            <NavBar />
            <main className="max-w-2xl mx-auto px-4 py-8">{children}</main>
          </AuthProvider>
        </DarkModeProvider>
      </body>
    </html>
  );
}
