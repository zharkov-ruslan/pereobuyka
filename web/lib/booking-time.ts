/** Instant из API: с Z / ±offset — как есть; без суффикса — UTC. */
function parseApiInstant(value: string): Date {
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$/.test(value)) {
    return new Date(`${value}Z`);
  }
  return new Date(value);
}

export function localTodayIsoDate(): string {
  const t = new Date();
  const y = t.getFullYear();
  const m = String(t.getMonth() + 1).padStart(2, "0");
  const d = String(t.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

/** Слот недоступен для новой записи: прошедший календарный день или сегодня, но время уже прошло. */
export function isPastBookingSlot(dayDate: string, slotStartsAtIso: string): boolean {
  const todayStr = localTodayIsoDate();
  if (dayDate < todayStr) {
    return true;
  }
  if (dayDate > todayStr) {
    return false;
  }
  return parseApiInstant(slotStartsAtIso).getTime() < Date.now();
}
