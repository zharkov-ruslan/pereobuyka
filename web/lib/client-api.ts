import { apiFetch } from "@/lib/api";
import type { WebUser } from "@/lib/auth";

export type AppointmentStatus = "scheduled" | "completed" | "cancelled";

export type ServiceLineItem = {
  service_id: string;
  quantity: number;
};

export type ServiceItem = {
  id: string;
  name: string;
  description: string;
  price: string;
  duration_minutes: number;
  is_active: boolean;
};

export type ServiceListResponse = {
  items: ServiceItem[];
};

export type LoyaltyRules = {
  max_bonus_spend_percent: number;
  earn_percent_after_visit: number;
};

export type SlotWindow = {
  starts_at: string;
  ends_at: string;
};

export type SlotListResponse = {
  items: SlotWindow[];
};

export type Appointment = {
  id: string;
  user_id: string;
  starts_at: string;
  ends_at: string;
  total_price: string;
  status: AppointmentStatus;
  created_at: string;
  service_items: ServiceLineItem[];
  source: string;
  discount_percent: number;
};

export type AppointmentListResponse = {
  items: Appointment[];
  total: number;
};

export type Visit = {
  id: string;
  appointment_id: string;
  total_amount: string;
  bonus_spent: number;
  bonus_earned: number;
  confirmed_at: string;
  confirmed_by_user_id: string;
  lines: ServiceLineItem[];
  client_rating_stars: number | null;
  client_rating_comment: string | null;
  service_rating_stars: number | null;
  service_rating_comment: string | null;
};

export type VisitListResponse = {
  items: Visit[];
  total: number;
};

export type BonusAccount = {
  id: string;
  user_id: string;
  balance: number;
};

export type ClientCabinetData = {
  me: WebUser;
  services: ServiceItem[];
  loyaltyRules: LoyaltyRules;
  bonusAccount: BonusAccount;
  appointments: Appointment[];
  visits: Visit[];
};

export async function fetchClientCabinetData(
  token: string,
): Promise<ClientCabinetData> {
  const [me, services, loyaltyRules, bonusAccount, appointments, visits] =
    await Promise.all([
      apiFetch<WebUser>("/api/v1/me", { token }),
      apiFetch<ServiceListResponse>("/api/v1/services?active_only=true"),
      apiFetch<LoyaltyRules>("/api/v1/loyalty/rules"),
      apiFetch<BonusAccount>("/api/v1/me/bonus-account", { token }),
      apiFetch<AppointmentListResponse>(
        "/api/v1/me/appointments?limit=100&offset=0",
        { token },
      ),
      apiFetch<VisitListResponse>("/api/v1/me/visits?limit=100&offset=0", {
        token,
      }),
    ]);

  return {
    me,
    services: services.items,
    loyaltyRules,
    bonusAccount,
    appointments: appointments.items,
    visits: visits.items,
  };
}

export async function fetchSlots(
  serviceIds: string[],
): Promise<SlotWindow[]> {
  const params = new URLSearchParams({
    date_from: getDateStringWithOffset(1),
    date_to: getDateStringWithOffset(14),
  });

  serviceIds.forEach((serviceId) => params.append("service_ids", serviceId));

  const response = await apiFetch<SlotListResponse>(
    `/api/v1/slots?${params.toString()}`,
  );

  return response.items;
}

export async function createClientAppointment(
  token: string,
  body: {
    starts_at: string;
    service_items: ServiceLineItem[];
    bonus_spend: number;
  },
): Promise<Appointment> {
  return apiFetch<Appointment>("/api/v1/appointments", {
    method: "POST",
    token,
    body: JSON.stringify(body),
  });
}

export async function cancelClientAppointment(
  token: string,
  appointmentId: string,
): Promise<Appointment> {
  return apiFetch<Appointment>(`/api/v1/me/appointments/${appointmentId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ status: "cancelled" }),
  });
}

export async function rateServiceVisit(
  token: string,
  visitId: string,
  stars: number,
  comment: string,
): Promise<Visit> {
  return apiFetch<Visit>(`/api/v1/me/visits/${visitId}/service-rating`, {
    method: "POST",
    token,
    body: JSON.stringify({
      stars,
      comment: comment.trim() || null,
    }),
  });
}

function getDateStringWithOffset(days: number) {
  const date = new Date();
  date.setDate(date.getDate() + days);

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}
