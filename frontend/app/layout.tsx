import type { Metadata } from "next";
import { Geist, Newsreader } from "next/font/google";
import { AppShell } from "@/components/app-shell/AppShell";
import "./globals.css";

const geist = Geist({
  subsets: ["latin"],
  variable: "--font-geist",
  display: "swap",
});

const newsreader = Newsreader({
  subsets: ["latin"],
  style: ["normal", "italic"],
  weight: ["400", "500", "600"],
  variable: "--font-newsreader",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Tablepick",
  description: "AI dining guide — filter the catalog, then rank a shortlist.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`dark ${geist.variable} ${newsreader.variable}`}>
      <head>
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
        />
      </head>
      <body className="bg-level-0 font-geist text-body-md text-on-surface antialiased">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
