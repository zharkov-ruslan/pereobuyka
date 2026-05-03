"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import {
  ArrowLeftIcon,
  CheckCircle2Icon,
  SaveIcon,
  SendIcon,
  XCircleIcon,
} from "lucide-react";

import { ClientRatingStarsInput } from "@/components/client-rating-stars";

import { ApiError } from "@/lib/api";
import {
  confirmAdminVisit,
  fetchAdminClientDetails,
  fetchAdminClients,
  rateAdminVisitClient,
  updateAdminAppointment,
  updateAdminVisit,
  type AdminAppointment,
  type AdminClient,
  type AdminClientDetailsData,
  type AppointmentStatus,
  type ServiceItem,
  type ServiceLineItem,
  type VisitResponse,
} from "@/lib/admin-api";
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

type ActiveTab = "appointments" | "visits";

type EditableLine = {
  service_id: string;
  quantity: string;
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

export default function AdminClientsPage() {
  const [token, setToken] = useState<string | null>(null);
  const [clients, setClients] = useState<AdminClient[]>([]);
  const [details, setDetails] = useState<AdminClientDetailsData | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>("appointments");
  const [showCancelled, setShowCancelled] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDetailsLoading, setIsDetailsLoading] = useState(false);

  const sortedClients = useMemo(
    () => [...clients].sort((a, b) => a.name.localeCompare(b.name, "ru")),
    [clients],
  );

  async function loadClients(currentToken: string) {
    setError(null);
    const response = await fetchAdminClients(currentToken);
    setClients(response.items);
  }

  async function loadDetails(currentToken: string, userId: string) {
    setIsDetailsLoading(true);
    setError(null);

    try {
      setDetails(await fetchAdminClientDetails(currentToken, userId));
      setActiveTab("appointments");
    } catch (currentError) {
      setError(getErrorMessage(currentError));
    } finally {
      setIsDetailsLoading(false);
    }
  }

  async function refreshSelectedDetails() {
    if (!token || !details) {
      return;
    }

    await Promise.all([loadClients(token), loadDetails(token, details.client.user_id)]);
  }

  useEffect(() => {
    queueMicrotask(() => {
      const session = loadAuthSession();
      if (!session || session.user.role !== "admin") {
        setError("Нужна локальная сессия администратора.");
        setIsLoading(false);
        return;
      }

      setToken(session.accessToken);
      loadClients(session.accessToken)
        .catch((currentError) => setError(getErrorMessage(currentError)))
        .finally(() => setIsLoading(false));
    });
  }, []);

  if (isLoading) {
    return <LoadingCards />;
  }

  return (
    <div className="flex flex-col gap-6">
      {error && (
        <Card>
          <CardHeader>
            <CardTitle>Не удалось выполнить действие</CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
        </Card>
      )}

      {details ? (
        <ClientDetails
          data={details}
          activeTab={activeTab}
          showCancelled={showCancelled}
          token={token}
          isLoading={isDetailsLoading}
          onBack={() => setDetails(null)}
          onChangeTab={setActiveTab}
          onToggleCancelled={() => setShowCancelled((value) => !value)}
          onSaved={() => {
            refreshSelectedDetails().catch((currentError) =>
              setError(getErrorMessage(currentError)),
            );
          }}
          onError={(message) => setError(message)}
        />
      ) : (
        <ClientTable
          clients={sortedClients}
          onSelect={(client) =>
            token &&
            loadDetails(token, client.user_id).catch((currentError) =>
              setError(getErrorMessage(currentError)),
            )
          }
        />
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
            <CardTitle>Загружаем клиентов</CardTitle>
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

function ClientTable({
  clients,
  onSelect,
}: {
  clients: AdminClient[];
  onSelect: (client: AdminClient) => void;
}) {
  if (clients.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Клиентов пока нет</CardTitle>
          <CardDescription>
            После seed или первых записей список появится здесь.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-4 pt-6">
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full min-w-[760px] text-sm">
            <thead className="bg-muted text-left text-muted-foreground">
              <tr>
                <th className="px-3 py-2 font-medium">Клиент</th>
                <th className="px-3 py-2 font-medium">Телефон</th>
                <th className="px-3 py-2 font-medium">Визиты</th>
                <th className="px-3 py-2 font-medium">Потрачено</th>
                <th className="px-3 py-2 font-medium">Бонусы</th>
                <th className="px-3 py-2 font-medium">Рейтинг</th>
                <th className="px-3 py-2 font-medium">Действие</th>
              </tr>
            </thead>
            <tbody>
              {clients.map((client) => (
                <tr
                  key={client.user_id}
                  className="cursor-pointer border-t transition-colors hover:bg-muted/60"
                  onDoubleClick={() => onSelect(client)}
                >
                  <td className="px-3 py-2 font-medium">{client.name}</td>
                  <td className="px-3 py-2 text-muted-foreground">
                    {client.phone ?? "Не указан"}
                  </td>
                  <td className="px-3 py-2">{client.visits_count}</td>
                  <td className="px-3 py-2">{formatMoney(client.total_spent)}</td>
                  <td className="px-3 py-2">{client.bonus_balance}</td>
                  <td className="px-3 py-2">{client.rating_avg ?? "Нет"}</td>
                  <td className="px-3 py-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => onSelect(client)}
                    >
                      Открыть
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function ClientDetails({
  data,
  activeTab,
  showCancelled,
  token,
  isLoading,
  onBack,
  onChangeTab,
  onToggleCancelled,
  onSaved,
  onError,
}: {
  data: AdminClientDetailsData;
  activeTab: ActiveTab;
  showCancelled: boolean;
  token: string | null;
  isLoading: boolean;
  onBack: () => void;
  onChangeTab: (tab: ActiveTab) => void;
  onToggleCancelled: () => void;
  onSaved: () => void;
  onError: (message: string) => void;
}) {
  const appointments = data.appointments.filter(
    (appointment) => appointment.status !== "completed",
  );
  const visibleAppointments = appointments.filter(
    (appointment) => showCancelled || appointment.status !== "cancelled",
  );
  const telegramHref = getTelegramHref(data.client);

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex flex-col gap-2">
              <Button type="button" variant="ghost" size="sm" onClick={onBack}>
                <ArrowLeftIcon data-icon="inline-start" />К списку клиентов
              </Button>
              <CardTitle>{data.client.name}</CardTitle>
              <CardDescription>
                {data.client.phone ?? "Телефон не указан"} · рейтинг{" "}
                {data.client.rating_avg ?? "нет"}
              </CardDescription>
            </div>
            <CardAction className="flex flex-wrap gap-2">
              <Badge variant="secondary">
                {data.client.visits_count} визитов
              </Badge>
              <Badge variant="outline">
                {formatMoney(data.client.total_spent)}
              </Badge>
              <Badge variant="outline">{data.client.bonus_balance} бонусов</Badge>
              {telegramHref && (
                <Button
                  variant="outline"
                  size="sm"
                  nativeButton={false}
                  render={<a href={telegramHref} />}
                >
                  <SendIcon data-icon="inline-start" />
                  Telegram
                </Button>
              )}
            </CardAction>
          </div>
        </CardHeader>
      </Card>

      <div className="flex flex-wrap items-center gap-2">
        <Button
          type="button"
          variant={activeTab === "appointments" ? "default" : "outline"}
          className={
            activeTab === "appointments"
              ? "shadow-sm"
              : "border-border bg-background"
          }
          onClick={() => onChangeTab("appointments")}
        >
          Записи
        </Button>
        <Button
          type="button"
          variant={activeTab === "visits" ? "default" : "outline"}
          className={
            activeTab === "visits"
              ? "shadow-sm"
              : "border-border bg-background"
          }
          onClick={() => onChangeTab("visits")}
        >
          Визиты
        </Button>
        {activeTab === "appointments" && (
          <Button type="button" variant="ghost" onClick={onToggleCancelled}>
            {showCancelled ? "Скрыть отменённые" : "Показать отменённые"}
          </Button>
        )}
        {isLoading && <Badge variant="outline">Обновление...</Badge>}
      </div>

      {activeTab === "appointments" ? (
        <div className="grid gap-4">
          {visibleAppointments.length === 0 ? (
            <EmptyCard title="Записей нет" description="Для клиента нет активных записей." />
          ) : (
            visibleAppointments.map((appointment) => (
              <AppointmentCard
                key={appointment.id}
                appointment={appointment}
                services={data.services}
                token={token}
                onSaved={onSaved}
                onError={onError}
              />
            ))
          )}
        </div>
      ) : (
        <div className="grid gap-4">
          {data.visits.length === 0 ? (
            <EmptyCard title="Визитов нет" description="Подтверждённых визитов пока нет." />
          ) : (
            data.visits.map((visit) => (
              <VisitCard
                key={visit.id}
                visit={visit}
                services={data.services}
                token={token}
                onSaved={onSaved}
                onError={onError}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
}

function AppointmentCard({
  appointment,
  services,
  token,
  onSaved,
  onError,
}: {
  appointment: AdminAppointment;
  services: ServiceItem[];
  token: string | null;
  onSaved: () => void;
  onError: (message: string) => void;
}) {
  const [lines, setLines] = useState(() => toEditableLines(appointment.service_items));
  const [discountPercent, setDiscountPercent] = useState(
    String(appointment.discount_percent),
  );
  const [isPending, startTransition] = useTransition();
  const total = calculateTotal(lines, services, Number(discountPercent) || 0);

  function handleSave(status?: AppointmentStatus) {
    if (!token) {
      return;
    }

    startTransition(async () => {
      try {
        await updateAdminAppointment(token, appointment.id, {
          status,
          service_items: normalizeLines(lines),
          discount_percent: clampPercent(discountPercent),
        });
        onSaved();
      } catch (currentError) {
        onError(getErrorMessage(currentError));
      }
    });
  }

  function handleConfirmVisit() {
    if (!token) {
      return;
    }

    startTransition(async () => {
      try {
        await confirmAdminVisit(token, appointment);
        onSaved();
      } catch (currentError) {
        onError(getErrorMessage(currentError));
      }
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{formatDateTime(appointment.starts_at)}</CardTitle>
        <CardDescription>
          {STATUS_LABELS[appointment.status]} · итог по форме {formatMoney(total)}
        </CardDescription>
        <CardAction>
          <Badge variant={getStatusBadgeVariant(appointment.status)}>
            {STATUS_LABELS[appointment.status]}
          </Badge>
        </CardAction>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <LineEditor lines={lines} services={services} onChange={setLines} />
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor={`discount-${appointment.id}`}>Скидка, %</FieldLabel>
            <Input
              id={`discount-${appointment.id}`}
              type="number"
              min={0}
              max={100}
              value={discountPercent}
              onChange={(event) => setDiscountPercent(event.target.value)}
            />
            <FieldDescription>
              Backend пересчитает длительность, итоговую сумму и начисление бонусов.
            </FieldDescription>
          </Field>
        </FieldGroup>
        <div className="flex flex-wrap gap-2">
          <Button type="button" disabled={isPending} onClick={() => handleSave()}>
            <SaveIcon data-icon="inline-start" />
            Сохранить правки
          </Button>
          {appointment.status === "scheduled" && (
            <>
              <Button
                type="button"
                variant="outline"
                disabled={isPending}
                onClick={handleConfirmVisit}
              >
                <CheckCircle2Icon data-icon="inline-start" />
                Подтвердить визит
              </Button>
              <Button
                type="button"
                variant="destructive"
                disabled={isPending}
                onClick={() => handleSave("cancelled")}
              >
                <XCircleIcon data-icon="inline-start" />
                Отменить запись
              </Button>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function VisitCard({
  visit,
  services,
  token,
  onSaved,
  onError,
}: {
  visit: VisitResponse;
  services: ServiceItem[];
  token: string | null;
  onSaved: () => void;
  onError: (message: string) => void;
}) {
  const [lines, setLines] = useState(() => toEditableLines(visit.lines));
  const [totalAmount, setTotalAmount] = useState(visit.total_amount);
  const [bonusSpent, setBonusSpent] = useState(String(visit.bonus_spent));
  const [bonusEarned, setBonusEarned] = useState(String(visit.bonus_earned));
  const [ratingStars, setRatingStars] = useState(visit.client_rating_stars ?? 5);
  const [ratingComment, setRatingComment] = useState(visit.client_rating_comment ?? "");
  const [isPending, startTransition] = useTransition();

  function handleSaveVisit() {
    if (!token) {
      return;
    }

    startTransition(async () => {
      try {
        await updateAdminVisit(token, visit.id, {
          lines: normalizeLines(lines),
          total_amount: totalAmount,
          bonus_spent: toNonNegativeInt(bonusSpent),
          bonus_earned: toNonNegativeInt(bonusEarned),
        });
        onSaved();
      } catch (currentError) {
        onError(getErrorMessage(currentError));
      }
    });
  }

  function handleSaveRating() {
    if (!token) {
      return;
    }

    startTransition(async () => {
      try {
        await rateAdminVisitClient(token, visit.id, ratingStars, ratingComment);
        onSaved();
      } catch (currentError) {
        onError(getErrorMessage(currentError));
      }
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{formatDateTime(visit.confirmed_at)}</CardTitle>
        <CardDescription>
          Оплачено {formatMoney(totalAmount)} · бонусы +{visit.bonus_earned} / -
          {visit.bonus_spent}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <LineEditor lines={lines} services={services} onChange={setLines} />
        <div className="grid gap-4 md:grid-cols-3">
          <Field>
            <FieldLabel htmlFor={`visit-total-${visit.id}`}>Оплачено</FieldLabel>
            <Input
              id={`visit-total-${visit.id}`}
              value={totalAmount}
              onChange={(event) => setTotalAmount(event.target.value)}
            />
          </Field>
          <Field>
            <FieldLabel htmlFor={`visit-spent-${visit.id}`}>Списано бонусов</FieldLabel>
            <Input
              id={`visit-spent-${visit.id}`}
              type="number"
              min={0}
              value={bonusSpent}
              onChange={(event) => setBonusSpent(event.target.value)}
            />
          </Field>
          <Field>
            <FieldLabel htmlFor={`visit-earned-${visit.id}`}>Начислено бонусов</FieldLabel>
            <Input
              id={`visit-earned-${visit.id}`}
              type="number"
              min={0}
              value={bonusEarned}
              onChange={(event) => setBonusEarned(event.target.value)}
            />
          </Field>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" disabled={isPending} onClick={handleSaveVisit}>
            <SaveIcon data-icon="inline-start" />
            Сохранить визит
          </Button>
        </div>

        <FieldGroup>
          <Field>
            <FieldLabel htmlFor={`rating-${visit.id}`}>Оценка клиента</FieldLabel>
            <ClientRatingStarsInput
              id={`rating-${visit.id}`}
              value={ratingStars}
              onChange={setRatingStars}
            />
          </Field>
          <Field>
            <FieldLabel htmlFor={`rating-comment-${visit.id}`}>Комментарий</FieldLabel>
            <Input
              id={`rating-comment-${visit.id}`}
              value={ratingComment}
              onChange={(event) => setRatingComment(event.target.value)}
            />
          </Field>
          <Button type="button" disabled={isPending} onClick={handleSaveRating}>
            <SaveIcon data-icon="inline-start" />
            Сохранить оценку
          </Button>
        </FieldGroup>
      </CardContent>
    </Card>
  );
}

function LineEditor({
  lines,
  services,
  onChange,
}: {
  lines: EditableLine[];
  services: ServiceItem[];
  onChange: (lines: EditableLine[]) => void;
}) {
  function updateLine(index: number, line: EditableLine) {
    onChange(lines.map((item, currentIndex) => (currentIndex === index ? line : item)));
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-medium">Услуги</span>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={services.length === 0}
          onClick={() =>
            onChange([
              ...lines,
              { service_id: services[0]?.id ?? "", quantity: "1" },
            ])
          }
        >
          Добавить услугу
        </Button>
      </div>
      {lines.map((line, index) => (
        <div key={`${line.service_id}-${index}`} className="grid gap-2 md:grid-cols-[1fr_8rem_auto]">
          <select
            className="h-8 rounded-lg border border-input bg-background px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
            value={line.service_id}
            onChange={(event) =>
              updateLine(index, { ...line, service_id: event.target.value })
            }
          >
            {services.map((service) => (
              <option key={service.id} value={service.id}>
                {service.name} · {formatMoney(service.price)}
              </option>
            ))}
          </select>
          <Input
            type="number"
            min={1}
            value={line.quantity}
            onChange={(event) =>
              updateLine(index, { ...line, quantity: event.target.value })
            }
          />
          <Button
            type="button"
            variant="ghost"
            onClick={() => onChange(lines.filter((_, currentIndex) => currentIndex !== index))}
          >
            Удалить
          </Button>
        </div>
      ))}
    </div>
  );
}

function EmptyCard({ title, description }: { title: string; description: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
    </Card>
  );
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

function toEditableLines(lines: ServiceLineItem[]): EditableLine[] {
  return lines.map((line) => ({
    service_id: line.service_id,
    quantity: String(line.quantity),
  }));
}

function normalizeLines(lines: EditableLine[]): ServiceLineItem[] {
  return lines
    .filter((line) => line.service_id)
    .map((line) => ({
      service_id: line.service_id,
      quantity: Math.max(1, Number.parseInt(line.quantity, 10) || 1),
    }));
}

function calculateTotal(
  lines: EditableLine[],
  services: ServiceItem[],
  discountPercent: number,
) {
  const serviceById = new Map(services.map((service) => [service.id, service]));
  const subtotal = lines.reduce((sum, line) => {
    const service = serviceById.get(line.service_id);
    const quantity = Number.parseInt(line.quantity, 10) || 1;

    return sum + Number(service?.price ?? 0) * quantity;
  }, 0);

  return subtotal * ((100 - Math.min(Math.max(discountPercent, 0), 100)) / 100);
}

function clampPercent(value: string) {
  return Math.min(Math.max(Number.parseInt(value, 10) || 0, 0), 100);
}

function toNonNegativeInt(value: string) {
  return Math.max(Number.parseInt(value, 10) || 0, 0);
}

function getTelegramHref(client: AdminClient) {
  if (client.telegram_username) {
    return `https://t.me/${client.telegram_username.replace(/^@/, "")}`;
  }

  if (client.telegram_id) {
    return `tg://user?id=${client.telegram_id}`;
  }

  return null;
}

function formatDateTime(value: string) {
  return DATE_TIME_FORMATTER.format(new Date(value));
}

function formatMoney(value: string | number) {
  return MONEY_FORMATTER.format(Number(value));
}

function getStatusBadgeVariant(status: AppointmentStatus) {
  if (status === "completed") {
    return "secondary";
  }

  if (status === "cancelled") {
    return "destructive";
  }

  return "outline";
}
