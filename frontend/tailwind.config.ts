import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        page: "var(--bg-page)",
        surface: "var(--surface-card)",
        primary: "var(--text-primary)",
        secondary: "var(--text-secondary)",
        muted: "var(--text-muted)",
        accent: "var(--accent)",
        "accent-soft": "var(--accent-soft)",
        border: "var(--border)",
        "code-bg": "var(--code-bg)",
        "code-text": "var(--code-text)",
      },
      fontFamily: {
        serif: ["var(--font-serif)", "Georgia", "serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      borderRadius: {
        DEFAULT: "8px",
        card: "12px",
      },
    },
  },
  plugins: [],
};

export default config;