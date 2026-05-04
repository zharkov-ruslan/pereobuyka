"use client";

import { MoonIcon, SunIcon } from "lucide-react";
import { useTheme } from "next-themes";
import { useSyncExternalStore } from "react";

import { cn } from "@/lib/utils";

function useIsClient(): boolean {
  return useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );
}

type ThemeToggleProps = {
  className?: string;
};

export function ThemeToggle({ className }: ThemeToggleProps) {
  const { theme, setTheme } = useTheme();
  const isClient = useIsClient();

  if (!isClient) {
    return (
      <div
        className={cn(
          "h-8 w-[7.75rem] rounded-lg border bg-muted opacity-60",
          className,
        )}
        aria-hidden="true"
      />
    );
  }

  return (
    <div
      className={cn(
        "inline-flex rounded-lg border border-border bg-muted/50 p-0.5",
        className,
      )}
      role="group"
      aria-label="Тема оформления"
    >
      <button
        type="button"
        onClick={() => setTheme("light")}
        className={cn(
          "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors sm:text-sm",
          theme === "light"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground",
        )}
        aria-pressed={theme === "light"}
      >
        <SunIcon className="size-3.5 shrink-0" aria-hidden="true" />
        <span>Светлая</span>
      </button>
      <button
        type="button"
        onClick={() => setTheme("dark")}
        className={cn(
          "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors sm:text-sm",
          theme === "dark"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground",
        )}
        aria-pressed={theme === "dark"}
      >
        <MoonIcon className="size-3.5 shrink-0" aria-hidden="true" />
        <span>Тёмная</span>
      </button>
    </div>
  );
}
