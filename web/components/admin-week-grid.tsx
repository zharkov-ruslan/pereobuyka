"use client";

import { useMemo } from "react";

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { isPastBookingSlot, localTodayIsoDate } from "@/lib/booking-time";
import { cn } from "@/lib/utils";
import type { WeekGridDay, WeekGridEvent, WeekGridSlot } from "@/lib/admin-api";

type AdminWeekGridProps = {
  days: WeekGridDay[];
  slotStepMinutes: number;
  onEventClick: (event: WeekGridEvent, slot: WeekGridSlot) => void;
  onFreeSlotClick?: (day: WeekGridDay, slot: WeekGridSlot) => void;
};

const DAY_FORMATTER = new Intl.DateTimeFormat("ru-RU", {
  weekday: "short",
  day: "2-digit",
  month: "2-digit",
});
const TIME_FORMATTER = new Intl.DateTimeFormat("ru-RU", {
  hour: "2-digit",
  minute: "2-digit",
});
const MONEY_FORMATTER = new Intl.NumberFormat("ru-RU", {
  style: "currency",
  currency: "RUB",
  maximumFractionDigits: 0,
});

/** Instant из API: с Z / ±offset — как есть; без суффикса — UTC. */
function parseApiInstant(value: string): Date {
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$/.test(value)) {
    return new Date(`${value}Z`);
  }
  return new Date(value);
}

/** Одна строка сетки = локальное время начала слота (минуты от 00:00), чтобы разные дни совпадали по горизонтали. */
function localMinutesSinceMidnight(iso: string): number {
  const d = parseApiInstant(iso);
  return d.getHours() * 60 + d.getMinutes();
}

function collectRowMinutesSorted(days: WeekGridDay[]): number[] {
  const seen = new Set<number>();
  for (const day of days) {
    for (const slot of day.slots) {
      seen.add(localMinutesSinceMidnight(slot.starts_at));
    }
  }
  return Array.from(seen).sort((a, b) => a - b);
}

function findSlotAtLocalMinutes(
  day: WeekGridDay,
  minutes: number,
): WeekGridSlot | null {
  return (
    day.slots.find(
      (s) => localMinutesSinceMidnight(s.starts_at) === minutes,
    ) ?? null
  );
}

function pickDisplayEvent(
  events: WeekGridEvent[],
): WeekGridEvent | null {
  if (!events.length) {
    return null;
  }
  const completed = events.find((e) => e.state === "completed");
  if (completed) {
    return completed;
  }
  const scheduled = events.find((e) => e.state === "scheduled");
  if (scheduled) {
    return scheduled;
  }
  return events[0];
}

type BodyCell =
  | { variant: "closed" }
  | { variant: "empty" }
  | { variant: "free" }
  | {
      variant: "event";
      event: WeekGridEvent;
      slot: WeekGridSlot;
      rowSpan: number;
    };

function buildBodyModel(days: WeekGridDay[]): {
  rowMinutesList: number[];
  cells: BodyCell[][];
  omit: boolean[][];
} {
  const rowMinutesList = collectRowMinutesSorted(days);
  const n = rowMinutesList.length;
  const d = days.length;
  if (n === 0) {
    return { rowMinutesList: [], cells: [], omit: [] };
  }

  const cells: BodyCell[][] = Array.from({ length: n }, () =>
    Array.from({ length: d }, () => ({ variant: "empty" as const })),
  );
  const omit: boolean[][] = Array.from({ length: n }, () =>
    Array.from({ length: d }, () => false),
  );

  for (let c = 0; c < d; c++) {
    const day = days[c];
    if (day.slots.length === 0) {
      for (let r = 0; r < n; r++) {
        cells[r][c] = { variant: "closed" };
      }
      continue;
    }

    let r = 0;
    while (r < n) {
      const slot = findSlotAtLocalMinutes(day, rowMinutesList[r]);
      if (!slot) {
        cells[r][c] = { variant: "empty" };
        r += 1;
        continue;
      }
      const ev = pickDisplayEvent(slot.events);
      if (!ev) {
        cells[r][c] = { variant: "free" };
        r += 1;
        continue;
      }

      let span = 1;
      while (r + span < n) {
        const nextSlot = findSlotAtLocalMinutes(day, rowMinutesList[r + span]);
        if (
          !nextSlot?.events.some((e) => e.appointment_id === ev.appointment_id)
        ) {
          break;
        }
        span += 1;
      }

      const lastRowSlot =
        span > 1
          ? findSlotAtLocalMinutes(day, rowMinutesList[r + span - 1])
          : slot;
      const mergedSlot: WeekGridSlot = {
        ...slot,
        ends_at: lastRowSlot?.ends_at ?? slot.ends_at,
      };

      cells[r][c] = {
        variant: "event",
        event: ev,
        slot: mergedSlot,
        rowSpan: span,
      };
      for (let k = 1; k < span; k++) {
        omit[r + k][c] = true;
      }
      r += span;
    }
  }

  return { rowMinutesList, cells, omit };
}

function formatDayHeader(value: string) {
  return DAY_FORMATTER.format(new Date(`${value}T00:00:00`));
}

function formatRowTime(minutes: number) {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return TIME_FORMATTER.format(new Date(2000, 0, 1, h, m));
}

function formatMoney(value: string) {
  return MONEY_FORMATTER.format(Number(value));
}

function tooltipStatusTitle(state: WeekGridEvent["state"]): string {
  if (state === "completed") {
    return "Подтверждено";
  }
  if (state === "cancelled") {
    return "Отменено";
  }
  return "Запланировано";
}

export function AdminWeekGrid({
  days,
  slotStepMinutes,
  onEventClick,
  onFreeSlotClick,
}: AdminWeekGridProps) {
  const { rowMinutesList, cells, omit } = useMemo(
    () => buildBodyModel(days),
    [days],
  );

  if (!rowMinutesList.length) {
    return (
      <p className="text-sm text-muted-foreground">
        На неделе нет слотов для отображения.
      </p>
    );
  }

  const todayIso = localTodayIsoDate();

  return (
    <div className="max-w-full overflow-x-auto rounded-lg ring-1 ring-border">
      <table className="w-full min-w-0 table-fixed border-collapse text-sm">
        <caption className="sr-only">
          Сетка загрузки по слотам {slotStepMinutes} минут, колонки — дни недели
        </caption>
        <colgroup>
          <col className="w-12 sm:w-14" />
          {days.map((day) => (
            <col key={day.date} />
          ))}
        </colgroup>
        <thead>
          <tr className="bg-muted/50">
            <th
              scope="col"
              className="sticky left-0 z-20 w-12 min-w-12 border border-border bg-muted/80 px-0.5 py-2 text-center text-xs font-bold text-foreground backdrop-blur-sm"
            >
              Время
            </th>
            {days.map((day) => {
              const isToday = day.date === todayIso;
              return (
              <th
                key={day.date}
                scope="col"
                className={cn(
                  "border border-border px-2 py-2 text-center text-xs font-semibold leading-tight",
                  isToday
                    ? "bg-neutral-300 font-semibold text-neutral-900 dark:bg-neutral-700 dark:text-neutral-50"
                    : "text-foreground",
                )}
              >
                {formatDayHeader(day.date)}
              </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {rowMinutesList.map((rowMinutes, rowIdx) => (
            <tr key={rowMinutes} className="group/row">
              <th
                scope="row"
                className="sticky left-0 z-10 w-12 min-w-12 border border-border bg-background px-0.5 py-0 text-center text-xs font-bold tabular-nums text-foreground backdrop-blur-sm"
              >
                <span className="block py-2">{formatRowTime(rowMinutes)}</span>
              </th>
              {days.map((day, colIdx) => {
                if (omit[rowIdx]?.[colIdx]) {
                  return null;
                }
                const cell = cells[rowIdx][colIdx];
                const rs =
                  cell.variant === "event" ? cell.rowSpan : 1;

                if (cell.variant === "closed") {
                  return (
                    <td
                      key={`${day.date}-${colIdx}-${rowIdx}`}
                      rowSpan={rs}
                      className="border border-border bg-muted/30 p-0"
                    >
                      <div className="flex min-h-10 items-stretch justify-center bg-muted/20" />
                    </td>
                  );
                }

                if (cell.variant === "empty") {
                  return (
                    <td
                      key={`${day.date}-${colIdx}-${rowIdx}`}
                      rowSpan={rs}
                      className="border border-border bg-muted/10 p-0"
                    >
                      <div className="min-h-10" />
                    </td>
                  );
                }

                if (cell.variant === "free") {
                  const slot = findSlotAtLocalMinutes(day, rowMinutesList[rowIdx]);
                  if (!slot) {
                    return (
                      <td
                        key={`${day.date}-${colIdx}-${rowIdx}`}
                        rowSpan={rs}
                        className="border border-border bg-background p-0"
                      >
                        <div className="min-h-10" />
                      </td>
                    );
                  }
                  const past = isPastBookingSlot(day.date, slot.starts_at);
                  return (
                    <td
                      key={`${day.date}-${colIdx}-${rowIdx}`}
                      rowSpan={rs}
                      className={cn(
                        "border border-border bg-background p-0",
                        !past && "transition-colors hover:bg-muted/50",
                        past && "bg-muted/20",
                      )}
                    >
                      {past || !onFreeSlotClick ? (
                        <div
                          className={cn(
                            "flex min-h-10 items-center justify-center px-0.5 py-1 text-center text-xs",
                            past
                              ? "cursor-default text-muted-foreground/70"
                              : "text-muted-foreground",
                          )}
                        >
                          {past ? "Прошло" : "Свободно"}
                        </div>
                      ) : (
                        <button
                          type="button"
                          className="flex min-h-10 w-full items-center justify-center px-0.5 py-1 text-center text-xs text-muted-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset"
                          onClick={() => onFreeSlotClick(day, slot)}
                        >
                          Свободно
                        </button>
                      )}
                    </td>
                  );
                }

                const { event, slot } = cell;
                const viz =
                  event.state === "completed"
                    ? "visit"
                    : event.state === "cancelled"
                      ? "cancelled"
                      : "scheduled";

                const cellLabel =
                  event.state === "completed"
                    ? "Визит"
                    : event.state === "cancelled"
                      ? "Отмена"
                      : "Запись";

                const cellClasses = cn(
                  "border border-border p-0 align-top transition-colors",
                  viz === "scheduled" &&
                    "bg-orange-500/15 hover:bg-orange-500/25 focus-within:bg-orange-500/25",
                  viz === "visit" &&
                    "bg-emerald-500/15 hover:bg-emerald-500/25 focus-within:bg-emerald-500/25",
                  viz === "cancelled" &&
                    "bg-muted/70 text-muted-foreground hover:bg-muted focus-within:bg-muted",
                );

                const tooltipBody = (
                  <div className="flex min-w-[11rem] max-w-xs flex-col gap-2 text-left">
                    <div className="flex flex-col gap-0.5">
                      <p className="text-[0.7rem] font-semibold leading-tight text-background">
                        {tooltipStatusTitle(event.state)}
                      </p>
                      <p className="text-[0.7rem] font-medium leading-tight text-background/90">
                        {event.client_name}
                      </p>
                    </div>
                    <ul className="list-inside list-disc text-[0.7rem] leading-snug">
                      {event.service_summaries.map((line) => (
                        <li key={line}>{line}</li>
                      ))}
                    </ul>
                    <p className="border-t border-background/20 pt-1 text-[0.7rem] font-medium">
                      Итого: {formatMoney(event.total_price)}
                    </p>
                    {onFreeSlotClick &&
                    event.state === "cancelled" &&
                    !isPastBookingSlot(day.date, slot.starts_at) ? (
                      <button
                        type="button"
                        className="mt-0.5 w-full rounded-md border border-background/35 bg-background/15 px-2 py-1.5 text-[0.7rem] font-medium text-background hover:bg-background/25"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          onFreeSlotClick(day, slot);
                        }}
                      >
                        Новая запись
                      </button>
                    ) : null}
                  </div>
                );

                return (
                  <td
                    key={`${day.date}-${colIdx}-${rowIdx}`}
                    rowSpan={rs}
                    className={cn(cellClasses, "relative min-h-10 p-0 align-top")}
                  >
                    <Tooltip>
                      <TooltipTrigger
                        render={
                          <button
                            type="button"
                            className="absolute inset-0 z-0 box-border flex items-center justify-center px-1 py-1 text-center text-xs font-medium text-foreground outline-none focus-visible:z-10 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset"
                            onClick={() => onEventClick(event, slot)}
                          >
                            {cellLabel}
                          </button>
                        }
                      />
                      <TooltipContent side="top" className="pointer-events-auto">
                        {tooltipBody}
                      </TooltipContent>
                    </Tooltip>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
