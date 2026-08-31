import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AIOS — One workspace, every model",
  description: "Chat, compare, and judge multiple AI providers from one conversation.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `try{const t=localStorage.getItem('theme');if(t==='dark'||(!t&&matchMedia('(prefers-color-scheme:dark)').matches))document.documentElement.setAttribute('data-theme','dark')}catch(e){}`,
          }}
        />
      </head>
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
