"use client";

import { useEffect, useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
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
import { ApiError, apiFetch } from "@/lib/api";
import {
  createAdminAppointment,
  createAdminClientQuick,
  fetchAdminClients,
  type AdminClient,
  type ServiceItem,
  type ServiceLineItem,
  type ServiceListResponse,
  type WeekGridSlot,
} from "@/lib/admin-api";

type LineDraft = { service_id: string; quantity: string };

type ClientMode = "existing" | "new";

export type AdminCreateBookingSheetProps = {
  token: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  dayLabel: string;
  timeLabel: string;
  slot: WeekGridSlot | null;
  onSuccess: () => void;
};

const MONEY_FORMATTER = new Intl.NumberFormat("ru-RU", {
  style: "currency",
  currency: "RUB",
  maximumFractionDigits: 0,
});

function formatMoney(value: string) {
  return MONEY_FORMATTER.format(Number(value));
}

function normalizeLines(lines: LineDraft[]): ServiceLineItem[] {
  return lines
    .filter((line) => line.service_id)
    .map((line) => ({
      service_id: line.service_id,
      quantity: Math.max(1, Number.parseInt(line.quantity, 10) || 1),
    }));
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

/** Размонтирование по `key` сбрасывает поля без setState в эффекте (react-hooks/set-state-in-effect). */
function AdminCreateBookingSheetBody({
  token,
  slot,
  onSuccess,
  onClose,
}: {
  token: string;
  slot: WeekGridSlot;
  onSuccess: () => void;
  onClose: () => void;
}) {
  const [clients, setClients] = useState<AdminClient[]>([]);
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [clientMode, setClientMode] = useState<ClientMode>("existing");
  const [selectedUserId, setSelectedUserId] = useState("");
  const [newName, setNewName] = useState("");
  const [newPhone, setNewPhone] = useState("");
  const [discountPercent, setDiscountPercent] = useState("0");
  const [lines, setLines] = useState<LineDraft[]>([]);
  const [isPending, startTransition] = useTransition();
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const [clientsRes, servicesRes] = await Promise.all([
          fetchAdminClients(token),
          apiFetch<ServiceListResponse>("/api/v1/admin/services?is_active=true", {
            token,
          }),
        ]);
        if (cancelled) {
          return;
        }
        setClients(clientsRes.items);
        const items = servicesRes.items;
        setServices(items);
        setLines(
          items.length
            ? [{ service_id: items[0].id, quantity: "1" }]
            : [],
        );
      } catch (e) {
        if (!cancelled) {
          setLoadError(getErrorMessage(e));
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [token, slot]);

  function updateLine(index: number, line: LineDraft) {
    setLines((prev) =>
      prev.map((item, i) => (i === index ? line : item)),
    );
  }

  function handleSubmit() {
    const items = normalizeLines(lines);
    if (!items.length) {
      setSubmitError("Добавьте хотя бы одну услугу.");
      return;
    }

    const disc = Math.min(Math.max(Number.parseInt(discountPercent, 10) || 0, 0), 100);

    startTransition(async () => {
      try {
        setSubmitError(null);
        let userId = selectedUserId;
        if (clientMode === "new") {
          if (!newName.trim()) {
            setSubmitError("Укажите имя нового клиента.");
            return;
          }
          const created = await createAdminClientQuick(token, {
            name: newName.trim(),
            phone: newPhone.trim() || null,
          });
          userId = created.user_id;
        } else if (!userId) {
          setSubmitError("Выберите клиента из списка.");
          return;
        }

        await createAdminAppointment(token, {
          user_id: userId,
          starts_at: slot.starts_at,
          service_items: items,
          discount_percent: disc,
        });
        onSuccess();
        onClose();
      } catch (e) {
        setSubmitError(getErrorMessage(e));
      }
    });
  }

  const previewSubtotal = lines.reduce((sum, line) => {
    const s = services.find((x) => x.id === line.service_id);
    const q = Number.parseInt(line.quantity, 10) || 1;
    return sum + Number(s?.price ?? 0) * q;
  }, 0);
  const discN = Math.min(Math.max(Number.parseInt(discountPercent, 10) || 0, 0), 100);
  const previewTotal = previewSubtotal * ((100 - discN) / 100);

  return (
    <>
        <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto overflow-x-hidden">
          {submitError ? (
            <p
              className="break-words rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
              role="alert"
            >
              {submitError}
            </p>
          ) : null}

          {loadError ? (
            <p className="text-sm text-destructive">{loadError}</p>
          ) : null}

          <FieldGroup>
              <Field>
                <FieldLabel>Клиент</FieldLabel>
                <div className="flex flex-wrap gap-2 py-1">
                  <Button
                    type="button"
                    size="sm"
                    variant={clientMode === "existing" ? "secondary" : "outline"}
                    onClick={() => setClientMode("existing")}
                  >
                    Из базы
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant={clientMode === "new" ? "secondary" : "outline"}
                    onClick={() => setClientMode("new")}
                  >
                    Новый клиент
                  </Button>
                </div>
              </Field>

              {clientMode === "existing" ? (
                <Field>
                  <FieldLabel htmlFor="booking-client-select">Выбор</FieldLabel>
                  <select
                    id="booking-client-select"
                    className="flex h-9 w-full min-w-0 rounded-lg border border-input bg-background py-2 pl-3 pr-10 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
                    value={selectedUserId}
                    onChange={(e) => setSelectedUserId(e.target.value)}
                  >
                    <option value="">— выберите —</option>
                    {clients.map((c) => (
                      <option key={c.user_id} value={c.user_id}>
                        {c.name}
                        {c.phone ? ` · ${c.phone}` : ""}
                      </option>
                    ))}
                  </select>
                  <FieldDescription>
                    Список до 100 клиентов. При необходимости заведите нового.
                  </FieldDescription>
                </Field>
              ) : (
                <>
                  <Field>
                    <FieldLabel htmlFor="booking-new-name">Имя</FieldLabel>
                    <Input
                      id="booking-new-name"
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                      placeholder="Иван Иванов"
                    />
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="booking-new-phone">Телефон</FieldLabel>
                    <Input
                      id="booking-new-phone"
                      value={newPhone}
                      onChange={(e) => setNewPhone(e.target.value)}
                      placeholder="+7 …"
                    />
                  </Field>
                </>
              )}

              <Field>
                <FieldLabel>Услуги</FieldLabel>
                <div className="flex flex-col gap-3 pt-1">
                  {lines.map((line, index) => (
                    <div
                      key={`${line.service_id}-${index}`}
                      className="flex min-w-0 flex-col gap-2 sm:flex-row sm:items-stretch"
                    >
                      <select
                        className="h-9 min-w-0 flex-1 rounded-lg border border-input bg-background py-2 pl-3 pr-10 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
                        value={line.service_id}
                        onChange={(e) =>
                          updateLine(index, { ...line, service_id: e.target.value })
                        }
                      >
                        {services.map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.name} · {formatMoney(s.price)}
                          </option>
                        ))}
                      </select>
                      <Input
                        type="number"
                        min={1}
                        className="h-9 w-11 shrink-0 px-0 text-center text-sm tabular-nums sm:w-10"
                        value={line.quantity}
                        onChange={(e) =>
                          updateLine(index, { ...line, quantity: e.target.value })
                        }
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="h-9 shrink-0 px-3 sm:self-stretch"
                        disabled={lines.length <= 1}
                        onClick={() =>
                          setLines((prev) => prev.filter((_, i) => i !== index))
                        }
                      >
                        Удалить
                      </Button>
                    </div>
                  ))}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={services.length === 0}
                    onClick={() =>
                      setLines((prev) => [
                        ...prev,
                        { service_id: services[0]?.id ?? "", quantity: "1" },
                      ])
                    }
                  >
                    Добавить услугу
                  </Button>
                </div>
              </Field>

              <Field>
                <FieldLabel htmlFor="booking-discount">Скидка, %</FieldLabel>
                <Input
                  id="booking-discount"
                  type="number"
                  min={0}
                  max={100}
                  value={discountPercent}
                  onChange={(e) => setDiscountPercent(e.target.value)}
                />
                <FieldDescription>
                  Ориентир по сумме: ~{formatMoney(String(Math.round(previewTotal)))}
                </FieldDescription>
              </Field>
            </FieldGroup>
        </div>

        <SheetFooter className="mt-auto shrink-0 flex flex-row flex-wrap justify-end gap-2 border-t border-border p-0 max-w-full pt-4">
          <Button
            type="button"
            variant="outline"
            disabled={isPending}
            onClick={onClose}
          >
            Отменить
          </Button>
          <Button
            type="button"
            disabled={isPending || !!loadError || services.length === 0}
            onClick={handleSubmit}
          >
            Записать
          </Button>
        </SheetFooter>
    </>
  );
}

export function AdminCreateBookingSheet({
  token,
  open,
  onOpenChange,
  dayLabel,
  timeLabel,
  slot,
  onSuccess,
}: AdminCreateBookingSheetProps) {
  const formKey = open && slot && token ? slot.starts_at : "booking-idle";

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="flex max-h-[100dvh] w-full max-w-[100vw] flex-col gap-4 overflow-hidden px-4 pb-6 pt-5 sm:max-w-md sm:px-5 sm:pt-6"
      >
        <SheetHeader className="shrink-0 space-y-1.5 p-0 pr-10 sm:pr-11">
          <SheetTitle>Новая запись</SheetTitle>
          <SheetDescription>
            {dayLabel} · {timeLabel}
          </SheetDescription>
        </SheetHeader>

        {open && slot && token ? (
          <AdminCreateBookingSheetBody
            key={formKey}
            token={token}
            slot={slot}
            onSuccess={onSuccess}
            onClose={() => onOpenChange(false)}
          />
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
