/**
 * Dark Mode Toggle Component
 * Switches between light and dark themes
 */
import { useEffect, useState } from "react";

export default function DarkModeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    // Apply dark mode class to document root
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  return (
    <button
      onClick={() => setDark((v) => !v)}
      className="px-3 py-2 rounded-xl bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 transition-colors text-sm font-medium"
      title={dark ? "Switch to Light Mode" : "Switch to Dark Mode"}
    >
      {dark ? "☀️ Light" : "🌙 Dark"}
    </button>
  );
}
