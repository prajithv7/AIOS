"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/auth";
import { Card, Button } from "@/components/ui";

export default function SettingsPage() {
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    setDarkMode(document.documentElement.getAttribute("data-theme") === "dark");
  }, []);

  function toggleTheme() {
    const next = !darkMode;
    setDarkMode(next);
    document.documentElement.setAttribute("data-theme", next ? "dark" : "light");
    localStorage.setItem("theme", next ? "dark" : "light");
  }

  return (
    <div className="mx-auto max-w-2xl p-8">
      <p className="eyebrow">Account</p>
      <h1 className="mt-2 text-2xl text-primary">Settings</h1>

      <Card className="mt-6">
        <p className="text-sm font-medium text-primary">Profile</p>
        <div className="mt-3 space-y-2 text-sm text-secondary">
          <p>Name: <span className="text-primary">{user?.name}</span></p>
          <p>Email: <span className="text-primary">{user?.email}</span></p>
        </div>
      </Card>

      <Card className="mt-4">
        <p className="text-sm font-medium text-primary">Appearance</p>
        <p className="mt-1 text-sm text-secondary">Toggle between light and dark theme.</p>
        <Button variant="secondary" className="mt-4" onClick={toggleTheme}>
          {darkMode ? "Switch to light mode" : "Switch to dark mode"}
        </Button>
      </Card>

      <Card className="mt-4">
        <p className="text-sm font-medium text-primary">Session</p>
        <p className="mt-1 text-sm text-secondary">Log out to clear your refresh token and end this session.</p>
        <Button
          variant="danger"
          className="mt-4"
          onClick={() => logout().then(() => router.push("/login"))}
        >
          Log out
        </Button>
      </Card>
    </div>
  );
}
