"use client";

import { useState } from "react";
import { StarIcon } from "lucide-react";

import { cn } from "@/lib/utils";

type ClientRatingStarsInputProps = {
  value: number;
  onChange: (stars: number) => void;
  id?: string;
};

export function ClientRatingStarsInput({
  value,
  onChange,
  id,
}: ClientRatingStarsInputProps) {
  const [hover, setHover] = useState<number | null>(null);
  const shown = hover ?? value;

  return (
    <div
      id={id}
      className="flex gap-0.5"
      onMouseLeave={() => setHover(null)}
      role="group"
      aria-label="Оценка от 1 до 5"
    >
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-amber-400/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          onMouseEnter={() => setHover(star)}
          onClick={() => onChange(star)}
          aria-label={`Оценка ${star} из 5`}
          aria-pressed={value === star}
        >
          <StarIcon
            className={cn(
              "size-7 transition-colors",
              star <= shown
                ? "fill-amber-400 text-amber-500 drop-shadow-sm"
                : "fill-transparent text-muted-foreground/45",
            )}
            strokeWidth={star <= shown ? 0 : 1.6}
          />
        </button>
      ))}
    </div>
  );
}
