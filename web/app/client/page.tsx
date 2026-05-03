"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import {
  CalendarClockIcon,
  CheckCircle2Icon,
  MessageCircleIcon,
  RefreshCwIcon,
  SaveIcon,
  SendIcon,
  StarIcon,
  WalletCardsIcon,
  XCircleIcon,
} from "lucide-react";

import { ApiError } from "@/lib/api";
import {
  cancelClientAppointment,
  createClientAppointment,
  fetchClientCabinetData,
  fetchSlots,
  rateServiceVisit,
  type Appointment,
  type AppointmentStatus,
  type ClientCabinetData,
  type ServiceItem,
  type ServiceLineItem,
  type SlotWindow,
  type Visit,
} from "@/lib/client-api";
import { loadAuthSession } from "@/lib/auth";
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
import { cn } from "@/lib/utils";

type AppointmentDraft = {
  version: 1;
  selectedServiceIds: string[];
  selectedSlotStartsAt: string | null;
  bonusSpend: number;
};

const DRAFT_STORAGE_KEY = "pereobuyka:web:appointment-draft:v1";
const TELEGRAM_BOT_URL = process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL;
const EMPTY_DRAFT: AppointmentDraft = {
  version: 1,
  selectedServiceIds: [],
  selectedSlotStartsAt: null,
  bonusSpend: 0,
};
const MONEY_FORMATTER = new Intl.NumberFormat("ru-RU", {
  style: "currency",
  currency: "RUB",
  maximumFractionDigits: 0,
});
const DATE_TIME_FORMATTER = new Intl.DateTimeFormat("ru-RU", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});
const STATUS_LABELS: Record<AppointmentStatus, string> = {
  scheduled: "Запись",
  completed: "Визит",
  cancelled: "Отмена",
};

export default function ClientPage() {
  const [token, setToken] = useState<string | null>(null);
  const [data, setData] = useState<ClientCabinetData | null>(null);
  const [draft, setDraft] = useState<AppointmentDraft>(EMPTY_DRAFT);
  const [slots, setSlots] = useState<SlotWindow[]>([]);
  const [showWizard, setShowWizard] = useState(false);
  const [showCancelled, setShowCancelled] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSlotsLoading, setIsSlotsLoading] = useState(false);
  const [isMutating, startMutation] = useTransition();

  const selectedServices = useMemo(() => {
    if (!data) {
      return [];
    }

    const selectedIds = new Set(draft.selectedServiceIds);
    return data.services.filter((service) => selectedIds.has(service.id));
  }, [data, draft.selectedServiceIds]);

  const selectedSlot = useMemo(() => {
    return (
      slots.find((slot) => slot.starts_at === draft.selectedSlotStartsAt) ?? null
    );
  }, [draft.selectedSlotStartsAt, slots]);

  const upcomingAppointments = useMemo(() => {
    return [...(data?.appointments ?? [])].sort(
      (a, b) =>
        new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime(),
    );
  }, [data?.appointments]);

  const visibleAppointments = showCancelled
    ? upcomingAppointments
    : upcomingAppointments.filter(
        (appointment) => appointment.status !== "cancelled",
      );

  const subtotal = selectedServices.reduce(
    (sum, service) => sum + Number(service.price),
    0,
  );
  const durationMinutes = selectedServices.reduce(
    (sum, service) => sum + service.duration_minutes,
    0,
  );
  const maxBonusSpend = data
    ? Math.min(
        data.bonusAccount.balance,
        Math.floor((subtotal * data.loyaltyRules.max_bonus_spend_percent) / 100),
      )
    : 0;
  const bonusSpend = Math.min(draft.bonusSpend, maxBonusSpend);
  const amountToPay = Math.max(subtotal - bonusSpend, 0);
  const bonusEarned = data
    ? Math.floor((amountToPay * data.loyaltyRules.earn_percent_after_visit) / 100)
    : 0;

  async function loadCabinet(currentToken: string) {
    setError(null);
    setData(await fetchClientCabinetData(currentToken));
  }

  function updateDraft(nextDraft: AppointmentDraft) {
    const normalizedDraft = {
      ...nextDraft,
      selectedServiceIds: Array.from(new Set(nextDraft.selectedServiceIds)),
      bonusSpend: Math.max(0, Math.floor(nextDraft.bonusSpend || 0)),
    };

    setDraft(normalizedDraft);
    saveDraft(normalizedDraft);
  }

  function toggleService(serviceId: string) {
    const hasService = draft.selectedServiceIds.includes(serviceId);
    updateDraft({
      ...draft,
      selectedServiceIds: hasService
        ? draft.selectedServiceIds.filter((id) => id !== serviceId)
        : [...draft.selectedServiceIds, serviceId],
      selectedSlotStartsAt: null,
    });
    setSlots([]);
  }

  async function loadAvailableSlots() {
    if (!draft.selectedServiceIds.length) {
      setError("Выберите хотя бы одну услугу.");
      return;
    }

    setIsSlotsLoading(true);
    setError(null);

    try {
      const nextSlots = await fetchSlots(draft.selectedServiceIds);
      setSlots(nextSlots);
      if (
        draft.selectedSlotStartsAt &&
        !nextSlots.some((slot) => slot.starts_at === draft.selectedSlotStartsAt)
      ) {
        updateDraft({ ...draft, selectedSlotStartsAt: null });
      }
    } catch (currentError) {
      setError(getErrorMessage(currentError));
    } finally {
      setIsSlotsLoading(false);
    }
  }

  function submitAppointment() {
    if (!token || !selectedSlot || !draft.selectedServiceIds.length) {
      setError("Выберите услуги и свободный слот.");
      return;
    }

    startMutation(async () => {
      try {
        await createClientAppointment(token, {
          starts_at: selectedSlot.starts_at,
          service_items: toServiceLineItems(draft.selectedServiceIds),
          bonus_spend: bonusSpend,
        });
        clearDraft();
        setDraft(EMPTY_DRAFT);
        setSlots([]);
        setShowWizard(false);
        await loadCabinet(token);
      } catch (currentError) {
        setError(getErrorMessage(currentError));
      }
    });
  }

  function cancelAppointment(appointmentId: string) {
    if (!token) {
      return;
    }

    startMutation(async () => {
      try {
        await cancelClientAppointment(token, appointmentId);
        await loadCabinet(token);
      } catch (currentError) {
        setError(getErrorMessage(currentError));
      }
    });
  }

  function handleRated() {
    if (!token) {
      return;
    }

    loadCabinet(token).catch((currentError) =>
      setError(getErrorMessage(currentError)),
    );
  }

  useEffect(() => {
    queueMicrotask(() => {
      const session = loadAuthSession();
      if (!session || session.user.role !== "client") {
        setError("Нужна локальная сессия.");
        setIsLoading(false);
        return;
      }

      setToken(session.accessToken);
      setDraft(loadDraft());
      loadCabinet(session.accessToken)
        .catch((currentError) => setError(getErrorMessage(currentError)))
        .finally(() => setIsLoading(false));
    });
  }, []);

  if (isLoading) {
    return <LoadingCards />;
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Личный кабинет недоступен</CardTitle>
          <CardDescription>
            {error ?? "Не удалось загрузить данные кабинета."}
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex flex-col gap-2">
          <h2 className="text-2xl font-semibold">
            {showWizard ? "Запись в сервис" : `Здравствуйте, ${data.me.name}`}
          </h2>
          {showWizard ? (
            <p className="text-sm text-muted-foreground">
              Выберите услуги, свободный слот и подтвердите запись.
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={!token}
            onClick={() =>
              token &&
              loadCabinet(token).catch((currentError) =>
                setError(getErrorMessage(currentError)),
              )
            }
          >
            <RefreshCwIcon data-icon="inline-start" />
            Обновить
          </Button>
        </div>
      </div>

      {error && (
        <Card>
          <CardHeader>
            <CardTitle>Не удалось выполнить действие</CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
        </Card>
      )}

      {showWizard ? (
        <AppointmentWizard
          bonusEarned={bonusEarned}
          bonusSpend={bonusSpend}
          data={data}
          draft={draft}
          durationMinutes={durationMinutes}
          isMutating={isMutating}
          isSlotsLoading={isSlotsLoading}
          maxBonusSpend={maxBonusSpend}
          selectedSlot={selectedSlot}
          selectedServices={selectedServices}
          slots={slots}
          subtotal={subtotal}
          onBack={() => setShowWizard(false)}
          onChangeBonus={(value) => updateDraft({ ...draft, bonusSpend: value })}
          onLoadSlots={() => {
            loadAvailableSlots();
          }}
          onSelectSlot={(slot) =>
            updateDraft({ ...draft, selectedSlotStartsAt: slot.starts_at })
          }
          onSubmit={submitAppointment}
          onToggleService={toggleService}
        />
      ) : (
        <>
          <ClientOverview
            appointmentDraft={draft}
            appointments={upcomingAppointments}
            bonusBalance={data.bonusAccount.balance}
            visits={data.visits}
            onStartWizard={() => setShowWizard(true)}
          />
          <AppointmentsCard
            appointments={visibleAppointments}
            isMutating={isMutating}
            services={data.services}
            showCancelled={showCancelled}
            onCancel={cancelAppointment}
            onToggleCancelled={() => setShowCancelled((value) => !value)}
          />
          <VisitsCard
            services={data.services}
            token={token}
            visits={data.visits}
            onRated={handleRated}
            onError={(message) => setError(message)}
          />
        </>
      )}
    </div>
  );
}

function LoadingCards() {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {Array.from({ length: 3 }).map((_, index) => (
        <Card key={index}>
          <CardHeader>
            <CardTitle>Загружаем кабинет</CardTitle>
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

function ClientOverview({
  appointmentDraft,
  appointments,
  bonusBalance,
  visits,
  onStartWizard,
}: {
  appointmentDraft: AppointmentDraft;
  appointments: Appointment[];
  bonusBalance: number;
  visits: Visit[];
  onStartWizard: () => void;
}) {
  const scheduledCount = appointments.filter(
    (appointment) => appointment.status === "scheduled",
  ).length;
  const hasDraft =
    appointmentDraft.selectedServiceIds.length > 0 ||
    Boolean(appointmentDraft.selectedSlotStartsAt);

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Card>
        <CardHeader>
          <CalendarClockIcon aria-hidden="true" />
          <CardTitle>Запись в сервис</CardTitle>
          <CardDescription>
            {hasDraft
              ? "Есть сохранённый черновик записи."
              : "Выберите услуги и свободное время."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button type="button" onClick={onStartWizard}>
            <CalendarClockIcon data-icon="inline-start" />
            {hasDraft ? "Продолжить запись" : "Запись в сервис"}
          </Button>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <WalletCardsIcon aria-hidden="true" />
          <CardTitle>История и бонусы</CardTitle>
          <CardDescription>
            {bonusBalance} бонусов, {visits.length} визитов
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Активных записей: {scheduledCount}. Отменённые скрыты по умолчанию.
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <MessageCircleIcon aria-hidden="true" />
          <CardTitle>Telegram-бот</CardTitle>
          <CardDescription>
            Быстрый переход к сценарию записи и консультациям в Telegram.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {TELEGRAM_BOT_URL ? (
            <a
              className="inline-flex h-8 items-center rounded-lg bg-primary px-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              href={TELEGRAM_BOT_URL}
              rel="noreferrer"
              target="_blank"
            >
              Открыть Telegram
            </a>
          ) : (
            <Button type="button" disabled>
              URL бота не задан
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function AppointmentWizard({
  bonusEarned,
  bonusSpend,
  data,
  draft,
  durationMinutes,
  isMutating,
  isSlotsLoading,
  maxBonusSpend,
  selectedSlot,
  selectedServices,
  slots,
  subtotal,
  onBack,
  onChangeBonus,
  onLoadSlots,
  onSelectSlot,
  onSubmit,
  onToggleService,
}: {
  bonusEarned: number;
  bonusSpend: number;
  data: ClientCabinetData;
  draft: AppointmentDraft;
  durationMinutes: number;
  isMutating: boolean;
  isSlotsLoading: boolean;
  maxBonusSpend: number;
  selectedSlot: SlotWindow | null;
  selectedServices: ServiceItem[];
  slots: SlotWindow[];
  subtotal: number;
  onBack: () => void;
  onChangeBonus: (value: number) => void;
  onLoadSlots: () => void;
  onSelectSlot: (slot: SlotWindow) => void;
  onSubmit: () => void;
  onToggleService: (serviceId: string) => void;
}) {
  const selectedIds = new Set(draft.selectedServiceIds);
  const amountToPay = Math.max(subtotal - bonusSpend, 0);

  return (
    <div className="flex flex-col gap-4">
      <div>
        <Button type="button" variant="outline" onClick={onBack}>
          На главную
        </Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(320px,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle>1. Услуги</CardTitle>
            <CardDescription>
              Черновик сохраняется в браузере после каждого изменения.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            {data.services.map((service) => {
              const isSelected = selectedIds.has(service.id);

              return (
                <button
                  key={service.id}
                  type="button"
                  className={cn(
                    "rounded-xl border bg-background p-4 text-left transition-colors hover:bg-muted",
                    isSelected && "border-primary bg-primary/5",
                  )}
                  onClick={() => onToggleService(service.id)}
                >
                  <span className="flex items-start justify-between gap-3">
                    <span className="font-medium">{service.name}</span>
                    {isSelected && <CheckCircle2Icon aria-hidden="true" />}
                  </span>
                  <span className="mt-2 block text-sm text-muted-foreground">
                    {service.duration_minutes} мин ·{" "}
                    {formatMoney(Number(service.price))}
                  </span>
                  {service.description && (
                    <span className="mt-2 block text-sm text-muted-foreground">
                      {service.description}
                    </span>
                  )}
                </button>
              );
            })}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Расчёт</CardTitle>
            <CardDescription>
              Итоговый пересчёт выполняет backend при создании записи.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <SummaryRow label="Услуг" value={String(selectedServices.length)} />
            <SummaryRow label="Длительность" value={`${durationMinutes} мин`} />
            <SummaryRow label="Стоимость" value={formatMoney(subtotal)} />
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="bonus-spend">Списать бонусы</FieldLabel>
                <Input
                  id="bonus-spend"
                  type="number"
                  min={0}
                  max={maxBonusSpend}
                  value={bonusSpend}
                  onChange={(event) =>
                    onChangeBonus(Number(event.target.value || 0))
                  }
                />
                <FieldDescription>
                  Максимум: {maxBonusSpend}. Баланс:{" "}
                  {data.bonusAccount.balance}.
                </FieldDescription>
              </Field>
            </FieldGroup>
            <SummaryRow label="К оплате" value={formatMoney(amountToPay)} />
            <SummaryRow label="Начислится" value={`${bonusEarned} бонусов`} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>2. Свободный слот</CardTitle>
          <CardDescription>
            Диапазон поиска: ближайшие 14 дней по выбранным услугам.
          </CardDescription>
          <CardAction>
            <Button
              type="button"
              variant="outline"
              disabled={!draft.selectedServiceIds.length || isSlotsLoading}
              onClick={onLoadSlots}
            >
              <RefreshCwIcon data-icon="inline-start" />
              {isSlotsLoading ? "Ищем..." : "Найти слоты"}
            </Button>
          </CardAction>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {slots.length ? (
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {slots.map((slot) => {
                const isSelected = slot.starts_at === selectedSlot?.starts_at;

                return (
                  <Button
                    key={slot.starts_at}
                    type="button"
                    variant={isSelected ? "default" : "outline"}
                    onClick={() => onSelectSlot(slot)}
                  >
                    {formatDateTime(slot.starts_at)}
                  </Button>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Выберите услуги и нажмите «Найти слоты».
            </p>
          )}

          <div className="flex flex-col gap-3 rounded-xl border bg-muted/40 p-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="font-medium">
                {selectedSlot
                  ? `Выбран слот ${formatDateTime(selectedSlot.starts_at)}`
                  : "Слот пока не выбран"}
              </p>
              <p className="text-sm text-muted-foreground">
                После успешного создания записи черновик будет очищен.
              </p>
            </div>
            <Button
              type="button"
              disabled={!selectedSlot || !draft.selectedServiceIds.length || isMutating}
              onClick={onSubmit}
            >
              <SendIcon data-icon="inline-start" />
              {isMutating ? "Создаём..." : "Подтвердить запись"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function AppointmentsCard({
  appointments,
  isMutating,
  services,
  showCancelled,
  onCancel,
  onToggleCancelled,
}: {
  appointments: Appointment[];
  isMutating: boolean;
  services: ServiceItem[];
  showCancelled: boolean;
  onCancel: (appointmentId: string) => void;
  onToggleCancelled: () => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Записи</CardTitle>
        <CardDescription>
          Предстоящие записи. Отменённые скрыты по умолчанию.
        </CardDescription>
        <CardAction>
          <Button type="button" variant="outline" onClick={onToggleCancelled}>
            {showCancelled ? "Скрыть отменённые" : "Показать отменённые"}
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {appointments.length ? (
          appointments.map((appointment) => (
            <Card key={appointment.id} size="sm">
              <CardHeader>
                <CardTitle>{formatDateTime(appointment.starts_at)}</CardTitle>
                <CardDescription>
                  {formatLines(appointment.service_items, services)}
                </CardDescription>
                <CardAction>
                  <Badge variant="outline">
                    {STATUS_LABELS[appointment.status]}
                  </Badge>
                </CardAction>
              </CardHeader>
              <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-muted-foreground">
                  {formatMoney(Number(appointment.total_price))} · скидка{" "}
                  {appointment.discount_percent}%
                </p>
                {appointment.status === "scheduled" && (
                  <Button
                    type="button"
                    variant="destructive"
                    disabled={isMutating}
                    onClick={() => onCancel(appointment.id)}
                  >
                    <XCircleIcon data-icon="inline-start" />
                    Отменить
                  </Button>
                )}
              </CardContent>
            </Card>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">
            Записей для отображения нет.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function VisitsCard({
  services,
  token,
  visits,
  onError,
  onRated,
}: {
  services: ServiceItem[];
  token: string | null;
  visits: Visit[];
  onError: (message: string) => void;
  onRated: () => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Визиты</CardTitle>
        <CardDescription>
          История подтверждённых визитов и оценка качества сервиса.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {visits.length ? (
          visits.map((visit) => (
            <Card key={visit.id} size="sm">
              <CardHeader>
                <CardTitle>{formatDateTime(visit.confirmed_at)}</CardTitle>
                <CardDescription>
                  {formatLines(visit.lines, services)}
                </CardDescription>
                <CardAction>
                  <Badge variant="outline">
                    {formatMoney(Number(visit.total_amount))}
                  </Badge>
                </CardAction>
              </CardHeader>
              <CardContent className="flex flex-col gap-4">
                <div className="grid gap-2 text-sm text-muted-foreground sm:grid-cols-3">
                  <span>Списано: {visit.bonus_spent}</span>
                  <span>Начислено: {visit.bonus_earned}</span>
                  <span>
                    Оценка:{" "}
                    {visit.service_rating_stars
                      ? `${visit.service_rating_stars}/5`
                      : "не выставлена"}
                  </span>
                </div>
                <VisitRatingForm
                  token={token}
                  visit={visit}
                  onError={onError}
                  onRated={onRated}
                />
              </CardContent>
            </Card>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">
            Подтверждённых визитов пока нет.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function VisitRatingForm({
  token,
  visit,
  onError,
  onRated,
}: {
  token: string | null;
  visit: Visit;
  onError: (message: string) => void;
  onRated: () => void;
}) {
  const [stars, setStars] = useState(visit.service_rating_stars ?? 5);
  const [comment, setComment] = useState(visit.service_rating_comment ?? "");
  const [isPending, startRating] = useTransition();

  function submitRating() {
    if (!token) {
      onError("Нужна локальная сессия.");
      return;
    }

    startRating(async () => {
      try {
        await rateServiceVisit(token, visit.id, stars, comment);
        onRated();
      } catch (currentError) {
        onError(getErrorMessage(currentError));
      }
    });
  }

  return (
    <FieldGroup>
      <Field>
        <FieldLabel>Оценка сервиса</FieldLabel>
        <div className="flex flex-wrap gap-2">
          {[1, 2, 3, 4, 5].map((value) => (
            <Button
              key={value}
              type="button"
              variant={stars === value ? "default" : "outline"}
              size="sm"
              onClick={() => setStars(value)}
            >
              <StarIcon data-icon="inline-start" />
              {value}
            </Button>
          ))}
        </div>
      </Field>
      <Field>
        <FieldLabel htmlFor={`visit-comment-${visit.id}`}>Комментарий</FieldLabel>
        <Input
          id={`visit-comment-${visit.id}`}
          value={comment}
          onChange={(event) => setComment(event.target.value)}
          placeholder="Опционально"
        />
      </Field>
      <div>
        <Button type="button" disabled={isPending} onClick={submitRating}>
          <SaveIcon data-icon="inline-start" />
          {isPending ? "Сохраняем..." : "Сохранить оценку"}
        </Button>
      </div>
    </FieldGroup>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

function toServiceLineItems(serviceIds: string[]): ServiceLineItem[] {
  return serviceIds.map((serviceId) => ({ service_id: serviceId, quantity: 1 }));
}

function formatLines(lines: ServiceLineItem[], services: ServiceItem[]) {
  const serviceById = new Map(services.map((service) => [service.id, service]));

  return lines
    .map((line) => {
      const service = serviceById.get(line.service_id);
      return `${service?.name ?? "Услуга"} × ${line.quantity}`;
    })
    .join(", ");
}

function formatMoney(value: number) {
  return MONEY_FORMATTER.format(value);
}

function formatDateTime(value: string) {
  return DATE_TIME_FORMATTER.format(new Date(value));
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

function loadDraft(): AppointmentDraft {
  if (typeof window === "undefined") {
    return EMPTY_DRAFT;
  }

  const raw = window.localStorage.getItem(DRAFT_STORAGE_KEY);
  if (!raw) {
    return EMPTY_DRAFT;
  }

  try {
    const parsed = JSON.parse(raw) as AppointmentDraft;
    if (parsed.version !== 1 || !Array.isArray(parsed.selectedServiceIds)) {
      throw new Error("Unsupported draft schema");
    }

    return {
      version: 1,
      selectedServiceIds: parsed.selectedServiceIds,
      selectedSlotStartsAt: parsed.selectedSlotStartsAt ?? null,
      bonusSpend: Number(parsed.bonusSpend) || 0,
    };
  } catch {
    window.localStorage.removeItem(DRAFT_STORAGE_KEY);
    return EMPTY_DRAFT;
  }
}

function saveDraft(draft: AppointmentDraft) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(draft));
}

function clearDraft() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(DRAFT_STORAGE_KEY);
}

