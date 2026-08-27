import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AIOS — One workspace, every model",
  description: "Chat, compare, and judge multiple AI providers from one conversation.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}