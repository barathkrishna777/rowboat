import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";

export const metadata: Metadata = {
  title: "Rowboat",
  description: "AI-powered group outing coordination",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 min-h-screen">
        <AuthProvider>
          <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
            <a href="/" className="text-xl font-bold text-orange-500">Rowboat</a>
            <div className="flex gap-4 text-sm">
              <a href="/profile" className="hover:text-orange-500">Profile</a>
              <a href="/friends" className="hover:text-orange-500">Friends</a>
              <a href="/swipe" className="hover:text-orange-500">Discover</a>
            </div>
          </nav>
          <main className="max-w-2xl mx-auto px-4 py-8">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
