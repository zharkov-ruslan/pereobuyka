"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  useTransition,
} from "react";
import {
  CalendarDaysIcon,
  CheckCircle2Icon,
  DatabaseIcon,
  MessageSquareTextIcon,
  XCircleIcon,
} from "lucide-react";

import { AdminCreateBookingSheet } from "@/components/admin-create-booking-sheet";
import { AdminWeekGrid } from "@/components/admin-week-grid";
import { ClientRatingStarsInput } from "@/components/client-rating-stars";
import { ApiError } from "@/lib/api";
import {
  cancelAdminAppointment,
  confirmAdminVisit,
  addDaysToDateString,
  fetchAdminDashboardData,
  getCurrentWeekStartDateString,
  postAdminDataInsight,
  rateAdminVisitClient,
  type AdminAppointment,
  type AdminDashboardData,
  type AdminDataInsightResponse,
  type WeekGridDay,
  type WeekGridEvent,
  type WeekGridSlot,
} from "@/lib/admin-api";
import { isPastBookingSlot } from "@/lib/booking-time";
import { loadAuthSession } from "@/lib/auth";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

type SelectedSlotEvent = {
  event: WeekGridEvent;
  slot: WeekGridSlot;
  appointment: AdminAppointment | null;
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

const WEEK_GRID_RANGE_FORMATTER = new Intl.DateTimeFormat("ru-RU", {
  day: "2-digit",
  month: "2-digit",
});

function formatWeekGridDateRangeSuffix(weekStartIso: string): string {
  const start = new Date(`${weekStartIso}T12:00:00`);
  const end = new Date(start);
  end.setDate(end.getDate() + 6);
  return ` с ${WEEK_GRID_RANGE_FORMATTER.format(start)} по ${WEEK_GRID_RANGE_FORMATTER.format(end)}`;
}

const STATUS_LABELS: Record<WeekGridEvent["state"], string> = {
  scheduled: "Запись",
  completed: "Визит",
  cancelled: "Отмена",
};

const SOURCE_LABELS: Record<string, string> = {
  admin: "Админ",
  llm: "LLM",
  telegram_bot: "Бот",
  web: "Web",
};

export default function AdminPage() {
  const [token, setToken] = useState<string | null>(null);
  const [data, setData] = useState<AdminDashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selected, setSelected] = useState<SelectedSlotEvent | null>(null);
  const [bookingDraft, setBookingDraft] = useState<{
    dayDate: string;
    slot: WeekGridSlot;
  } | null>(null);
  const [ratingStars, setRatingStars] = useState(5);
  const [ratingComment, setRatingComment] = useState("");
  const [nlQuestion, setNlQuestion] = useState("");
  const [nlError, setNlError] = useState<string | null>(null);
  const [nlResult, setNlResult] = useState<AdminDataInsightResponse | null>(null);
  const [isMutating, startMutation] = useTransition();

  const appointmentById = useMemo(() => {
    return new Map(
      data?.appointments.map((appointment) => [appointment.id, appointment]) ??
        [],
    );
  }, [data?.appointments]);

  const dataRef = useRef(data);

  useEffect(() => {
    dataRef.current = data;
  }, [data]);

  const kpiItems = useMemo(() => {
    if (!data) {
      return [];
    }

    return [
      {
        label: "Записи сегодня",
        value: data.today.appointments_total,
        icon: CalendarDaysIcon,
      },
      {
        label: "Подтверждённые визиты",
        value: data.today.visits_total,
        icon: CheckCircle2Icon,
      },
      {
        label: "Отмены",
        value: data.today.cancellations_total,
        icon: XCircleIcon,
      },
      {
        label: "Вопросы боту за 7 дней",
        value: data.today.consultation_user_messages_last_7_days,
        icon: MessageSquareTextIcon,
      },
    ];
  }, [data]);

  const loadDashboard = useCallback(
    async (
      currentToken: string,
      options?: { weekStart?: string; useGlobalLoader?: boolean },
    ) => {
      const snapshot = dataRef.current;
      const useGlobalLoader = options?.useGlobalLoader ?? snapshot === null;
      if (useGlobalLoader) {
        setIsLoading(true);
      }
      setError(null);

      try {
        const weekStart =
          options?.weekStart ??
          snapshot?.weekGrid.week_start ??
          getCurrentWeekStartDateString();
        setData(await fetchAdminDashboardData(currentToken, weekStart));
      } catch (currentError) {
        setError(getErrorMessage(currentError));
      } finally {
        if (useGlobalLoader) {
          setIsLoading(false);
        }
      }
    },
    [],
  );

  useEffect(() => {
    queueMicrotask(() => {
      const session = loadAuthSession();
      if (!session || session.user.role !== "admin") {
        setError("Нужна локальная сессия администратора.");
        setIsLoading(false);
        return;
      }

      setToken(session.accessToken);
      void loadDashboard(session.accessToken, { useGlobalLoader: true });
    });
  }, [loadDashboard]);

  function handleSelectEvent(event: WeekGridEvent, slot: WeekGridSlot) {
    setRatingStars(event.client_rating_stars ?? 5);
    setRatingComment(event.client_rating_comment ?? "");
    setSelected({
      event,
      slot,
      appointment: appointmentById.get(event.appointment_id) ?? null,
    });
  }

  function handleFreeSlot(day: WeekGridDay, slot: WeekGridSlot) {
    if (isPastBookingSlot(day.date, slot.starts_at)) {
      return;
    }
    setBookingDraft({ dayDate: day.date, slot });
  }

  function handleCancelAppointment() {
    if (!token || !selected) {
      return;
    }

    startMutation(async () => {
      const weekAtStart =
        data?.weekGrid.week_start ?? getCurrentWeekStartDateString();
      try {
        await cancelAdminAppointment(token, selected.event.appointment_id);
        setSelected(null);
        await loadDashboard(token, { weekStart: weekAtStart });
      } catch (currentError) {
        setError(getErrorMessage(currentError));
      }
    });
  }

  function handleConfirmVisit() {
    const currentSelection = selected;
    const appointment = currentSelection?.appointment;

    if (!token || !currentSelection || !appointment) {
      return;
    }

    startMutation(async () => {
      const weekAtStart =
        data?.weekGrid.week_start ?? getCurrentWeekStartDateString();
      try {
        const visit = await confirmAdminVisit(token, appointment);
        setSelected({
          ...currentSelection,
          event: {
            ...currentSelection.event,
            state: "completed",
            visit_id: visit.id,
            client_rating_stars: visit.client_rating_stars,
            client_rating_comment: visit.client_rating_comment,
          },
        });
        await loadDashboard(token, { weekStart: weekAtStart });
      } catch (currentError) {
        setError(getErrorMessage(currentError));
      }
    });
  }

  function handleRateClient() {
    const visitId = selected?.event.visit_id;
    if (!token || !visitId) {
      return;
    }

    const stars = ratingStars;
    const comment = ratingComment;

    startMutation(async () => {
      const weekAtStart =
        data?.weekGrid.week_start ?? getCurrentWeekStartDateString();
      try {
        setError(null);
        await rateAdminVisitClient(token, visitId, stars, comment);
        setSelected(null);
        await loadDashboard(token, { weekStart: weekAtStart });
      } catch (currentError) {
        setError(getErrorMessage(currentError));
      }
    });
  }

  function handleNlDataInsight() {
    if (!token || !nlQuestion.trim()) {
      return;
    }
    startMutation(async () => {
      setNlError(null);
      setNlResult(null);
      try {
        setNlResult(await postAdminDataInsight(token, nlQuestion));
      } catch (currentError) {
        setNlError(getErrorMessage(currentError));
      }
    });
  }

  function shiftDashboardWeek(deltaDays: number) {
    if (!token || !data) {
      return;
    }
    const nextStart = addDaysToDateString(data.weekGrid.week_start, deltaDays);
    startMutation(async () => {
      try {
        setError(null);
        setData(await fetchAdminDashboardData(token, nextStart));
      } catch (currentError) {
        setError(getErrorMessage(currentError));
      }
    });
  }

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Card key={index}>
            <CardHeader>
              <CardTitle>Загружаем данные</CardTitle>
              <CardDescription>Обращаемся к backend API.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-12 rounded-lg bg-muted" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {error && (
        <Card>
          <CardHeader>
            <CardTitle>Не удалось загрузить данные</CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
        </Card>
      )}

      {data ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {kpiItems.map((item) => {
              const Icon = item.icon;

              return (
                <Card key={item.label}>
                  <CardHeader>
                    <CardTitle>{item.label}</CardTitle>
                    <CardAction>
                      <Icon aria-hidden="true" />
                    </CardAction>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-semibold">{item.value}</div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <DatabaseIcon className="h-5 w-5 shrink-0" aria-hidden />
                Вопрос к данным
              </CardTitle>
              <CardDescription>
                Коротко опишите, что посчитать или найти по клиентам, записям и визитам. Выполняется
                только безопасное чтение (SELECT с ограничениями); нужен ключ LLM на сервере.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <FieldGroup className="gap-2">
                <Field>
                  <FieldLabel htmlFor="admin-nl-sql">Формулировка</FieldLabel>
                  <textarea
                    id="admin-nl-sql"
                    rows={3}
                    value={nlQuestion}
                    onChange={(e) => setNlQuestion(e.target.value)}
                    disabled={isMutating}
                    placeholder='Например: сколько пользователей с ролью "client"?'
                    className={cn(
                      "min-h-[5rem] w-full resize-y rounded-lg border border-input bg-transparent px-2.5 py-2 text-sm transition-colors outline-none",
                      "placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50",
                      "disabled:pointer-events-none disabled:opacity-50 dark:bg-input/30",
                    )}
                  />
                </Field>
              </FieldGroup>
              <div className="flex flex-wrap items-center gap-2">
                <Button
                  type="button"
                  disabled={!token || isMutating || !nlQuestion.trim()}
                  onClick={() => handleNlDataInsight()}
                >
                  {isMutating ? "Запрос…" : "Отправить"}
                </Button>
                {nlResult?.truncated ? (
                  <Badge variant="secondary">Строки обрезаны по лимиту</Badge>
                ) : null}
              </div>
              {nlError ? (
                <p className="text-sm text-destructive" role="alert">
                  {nlError}
                </p>
              ) : null}
              {nlResult ? (
                <div className="flex flex-col gap-3 text-sm">
                  <div>
                    <p className="font-medium text-foreground">Ответ</p>
                    <p className="mt-1 whitespace-pre-wrap text-muted-foreground">
                      {nlResult.summary}
                    </p>
                  </div>
                  <details className="rounded-lg border border-border bg-muted/40 px-3 py-2">
                    <summary className="cursor-pointer text-xs font-medium">
                      Показать SQL
                    </summary>
                    <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-all text-xs">
                      {nlResult.sql_executed}
                    </pre>
                  </details>
                  {nlResult.rows.length > 0 ? (
                    <div className="overflow-auto rounded-lg border border-border">
                      <table className="w-full min-w-[280px] border-collapse text-xs">
                        <thead className="bg-muted/60">
                          <tr>
                            {nlResult.columns.map((column) => (
                              <th
                                key={column}
                                className="border-b border-border px-2 py-1.5 text-left font-medium"
                              >
                                {column}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {nlResult.rows.slice(0, 20).map((row, rowIndex) => (
                            <tr key={rowIndex} className="odd:bg-background even:bg-muted/25">
                              {nlResult.columns.map((column) => (
                                <td
                                  key={`${rowIndex}-${column}`}
                                  className="border-b border-border px-2 py-1.5 align-top"
                                >
                                  {formatNlPreviewCell(row[column])}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-4">
            <Card className="min-w-0 xl:col-span-3">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-normal leading-snug sm:text-lg">
                  <span className="font-bold">Сетка недели</span>
                  {formatWeekGridDateRangeSuffix(data.weekGrid.week_start)}
                </CardTitle>
                <CardAction className="flex max-w-full flex-wrap justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={!token || isMutating}
                    onClick={() => shiftDashboardWeek(-7)}
                  >
                    Предыдущая неделя
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={!token || isMutating}
                    onClick={() => shiftDashboardWeek(7)}
                  >
                    Следующая неделя
                  </Button>
                </CardAction>
              </CardHeader>
              <CardContent className="p-4 pt-2">
                {data.weekGrid.days.some((day) => day.slots.length > 0) ? (
                  <AdminWeekGrid
                    days={data.weekGrid.days}
                    slotStepMinutes={data.weekGrid.slot_step_minutes}
                    onEventClick={handleSelectEvent}
                    onFreeSlotClick={handleFreeSlot}
                  />
                ) : (
                  <p className="px-4 py-6 text-sm text-muted-foreground">
                    На неделе нет слотов для отображения.
                  </p>
                )}
              </CardContent>
            </Card>

            <div className="flex min-w-0 flex-col gap-4 xl:col-span-1">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle>Источники записей сегодня</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col gap-3">
                  {Object.values(
                    data.today.bookings_scheduled_today_by_source,
                  ).every((n) => n === 0) ? (
                    <p className="text-sm text-muted-foreground">
                      Сегодня новых записей нет.
                    </p>
                  ) : (
                    Object.entries(
                      data.today.bookings_scheduled_today_by_source,
                    ).map(([source, count]) => (
                      <div
                        key={source}
                        className="flex items-center justify-between gap-3"
                      >
                        <span className="text-sm">
                          {SOURCE_LABELS[source] ?? source}
                        </span>
                        <Badge variant="secondary">{count}</Badge>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle>Статистика недели</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col gap-3">
                  {data.analytics.days.map((day) => {
                    const visits = day.visits_count;
                    const cancels = day.cancellations_count;
                    const total = visits + cancels;

                    return (
                      <div key={day.date} className="flex flex-col gap-1">
                      <div className="flex items-center justify-between gap-3 text-sm">
                        <span>{formatDay(day.date)}</span>
                        <span className="text-muted-foreground">
                          {visits} виз. / {cancels} отм.
                        </span>
                      </div>
                      <div className="flex h-2 w-full overflow-hidden rounded-full bg-muted">
                        {total === 0 ? (
                          <div
                            className="h-full w-full rounded-full bg-muted"
                            aria-hidden
                          />
                        ) : (
                          <>
                            <div
                              className="h-full shrink-0 bg-emerald-500 transition-[width]"
                              style={{ width: `${(visits / total) * 100}%` }}
                              title={`Визиты: ${visits}`}
                            />
                            <div
                              className="h-full shrink-0 bg-red-300 dark:bg-red-400/80"
                              style={{ width: `${(cancels / total) * 100}%` }}
                              title={`Отмены: ${cancels}`}
                            />
                          </>
                        )}
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {formatMoney(day.revenue_amount)}
                      </span>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle>Топ услуг за неделю</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col gap-2">
                  {data.analytics.top_services.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      Пока нет данных по услугам.
                    </p>
                  ) : (
                    data.analytics.top_services.map((service) => (
                      <div
                        key={service.service_id}
                        className="flex items-center justify-between gap-3"
                      >
                        <span className="truncate text-sm">{service.name}</span>
                        <Badge variant="outline">
                          {service.bookings_count}
                        </Badge>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </>
      ) : null}

      <AdminCreateBookingSheet
        token={token}
        open={bookingDraft !== null}
        onOpenChange={(next) => {
          if (!next) {
            setBookingDraft(null);
          }
        }}
        dayLabel={bookingDraft ? formatDay(bookingDraft.dayDate) : ""}
        timeLabel={
          bookingDraft
            ? `${formatTime(bookingDraft.slot.starts_at)}–${formatTime(bookingDraft.slot.ends_at)}`
            : ""
        }
        slot={bookingDraft?.slot ?? null}
        onSuccess={() => {
          if (token && data) {
            void loadDashboard(token, { weekStart: data.weekGrid.week_start });
          }
        }}
      />

      <Sheet
        open={selected !== null}
        onOpenChange={(open) => {
          if (!open) {
            setSelected(null);
          }
        }}
      >
        <SheetContent className="sm:max-w-md">
          {selected && (
            <>
              <SheetHeader>
                <SheetTitle>{selected.event.client_name}</SheetTitle>
                <SheetDescription>
                  {formatTime(
                    selected.appointment?.starts_at ??
                      selected.slot.starts_at,
                  )}
                  –
                  {formatTime(
                    selected.appointment?.ends_at ?? selected.slot.ends_at,
                  )}{" "}
                  · {STATUS_LABELS[selected.event.state]}
                </SheetDescription>
              </SheetHeader>

              <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-4">
                <div className="flex flex-wrap gap-2">
                  <Badge variant={getStatusBadgeVariant(selected.event.state)}>
                    {STATUS_LABELS[selected.event.state]}
                  </Badge>
                  <Badge variant="outline">
                    {formatMoney(selected.event.total_price)}
                  </Badge>
                  {selected.appointment && (
                    <Badge variant="secondary">
                      {SOURCE_LABELS[selected.appointment.source] ??
                        selected.appointment.source}
                    </Badge>
                  )}
                </div>

                <Card size="sm">
                  <CardHeader>
                    <CardTitle>Услуги</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="flex flex-col gap-2 text-sm">
                      {selected.event.service_summaries.map((summary) => (
                        <li key={summary}>{summary}</li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>

                {selected.event.visit_id ? (
                  <FieldGroup>
                    <Field>
                      <FieldLabel htmlFor="client-rating-stars">
                        Оценка клиента
                      </FieldLabel>
                      <ClientRatingStarsInput
                        id="client-rating-stars"
                        value={ratingStars}
                        onChange={setRatingStars}
                      />
                      <FieldDescription>
                        Оценка сохраняется в визите и видна администратору.
                      </FieldDescription>
                    </Field>
                    <Field>
                      <FieldLabel htmlFor="client-rating-comment">
                        Комментарий
                      </FieldLabel>
                      <Input
                        id="client-rating-comment"
                        value={ratingComment}
                        onChange={(event) =>
                          setRatingComment(event.target.value)
                        }
                        placeholder="Например: приехал вовремя"
                      />
                    </Field>
                  </FieldGroup>
                ) : null}
              </div>

              <SheetFooter>
                {selected.event.state === "scheduled" && (
                  <>
                    <Button
                      type="button"
                      variant="destructive"
                      disabled={isMutating}
                      onClick={handleCancelAppointment}
                    >
                      Отменить запись
                    </Button>
                    <Button
                      type="button"
                      disabled={isMutating || !selected.appointment}
                      onClick={handleConfirmVisit}
                    >
                      Подтвердить визит
                    </Button>
                  </>
                )}
                {selected.event.visit_id && (
                  <Button
                    type="button"
                    disabled={isMutating}
                    onClick={handleRateClient}
                  >
                    Сохранить оценку
                  </Button>
                )}
              </SheetFooter>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}

function formatNlPreviewCell(value: unknown): string {
  if (value === null || value === undefined) {
    return "—";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function getErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Неизвестная ошибка.";
}

function formatDay(value: string) {
  return DAY_FORMATTER.format(new Date(`${value}T00:00:00`));
}

/** Instant из API: с Z / ±offset — как есть; без суффикса — UTC (совместимость со старым week-grid). */
function parseApiInstant(value: string): Date {
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$/.test(value)) {
    return new Date(`${value}Z`);
  }
  return new Date(value);
}

function formatTime(value: string) {
  return TIME_FORMATTER.format(parseApiInstant(value));
}

function formatMoney(value: string) {
  return MONEY_FORMATTER.format(Number(value));
}

function getStatusBadgeVariant(state: WeekGridEvent["state"]) {
  if (state === "completed") {
    return "secondary";
  }

  if (state === "cancelled") {
    return "destructive";
  }

  return "outline";
}

