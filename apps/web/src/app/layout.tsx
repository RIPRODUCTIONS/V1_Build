import ImportCsvButton from "@/components/ImportCsvButton";
import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Atomic Console",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-screen text-gray-100">
        <header className="border-b atomic-surface">
          <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
            <div
              className="text-lg font-semibold tracking-tight"
              style={{ fontFamily: "var(--font-head)" }}
            >
              ATOMIC
            </div>
            <nav className="flex items-center gap-4 text-sm">
              <a className="hover:underline" href="/dashboard">
                Nucleus
              </a>
              <a className="hover:underline" href="/automation">
                Shells
              </a>
              <a className="hover:underline" href="/marketplace">
                Electrons
              </a>
              <a className="hover:underline" href="/investigations">
                Investigations
              </a>
              <a className="hover:underline" href="/personal">
                Personal
              </a>
              <ImportCsvButton />
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-4 py-6">
          <Providers>{children}</Providers>
        </main>
      </body>
    </html>
  );
}
