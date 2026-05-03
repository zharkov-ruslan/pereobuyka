import { apiFetch } from "@/lib/api";

export type AppointmentStatus = "scheduled" | "completed" | "cancelled";

export type ServiceLineItem = {
  service_id: string;
  quantity: number;
};

export type AdminClient = {
  user_id: string;
  name: string;
  phone: string | null;
  telegram_id: number | null;
  telegram_username: string | null;
  visits_count: number;
  total_spent: string;
  bonus_balance: number;
  rating_avg: string | null;
};

export type AdminClientListResponse = {
  items: AdminClient[];
  total: number;
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

export type DashboardTodayResponse = {
  date: string;
  appointments_total: number;
  visits_total: number;
  cancellations_total: number;
  bookings_scheduled_today_by_source: Record<string, number>;
  consultation_user_messages_last_7_days: number;
};

export type WeekGridEvent = {
  state: AppointmentStatus;
  appointment_id: string;
  visit_id: string | null;
  total_price: string;
  client_name: string;
  service_summaries: string[];
  client_rating_stars: number | null;
  client_rating_comment: string | null;
};

export type WeekGridSlot = {
  starts_at: string;
  ends_at: string;
  events: WeekGridEvent[];
};

export type WeekGridDay = {
  date: string;
  slots: WeekGridSlot[];
};

export type WeekGridResponse = {
  week_start: string;
  slot_step_minutes: number;
  days: WeekGridDay[];
};

export type AnalyticsWeekDay = {
  date: string;
  appointments_count: number;
  visits_count: number;
  cancellations_count: number;
  revenue_amount: string;
  bookings_by_source: Record<string, number>;
};

export type TopServiceStat = {
  service_id: string;
  name: string;
  bookings_count: number;
};

export type AnalyticsWeekResponse = {
  week_start: string;
  top_services: TopServiceStat[];
  days: AnalyticsWeekDay[];
};

export type AdminAppointment = {
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
  user: {
    id: string;
    name: string;
    phone: string | null;
    role: "admin" | "client";
    telegram_id: number | null;
    telegram_username: string | null;
    registered_at: string;
    source: string;
  } | null;
};

export type AdminAppointmentListResponse = {
  items: AdminAppointment[];
  total: number;
};

export type VisitResponse = {
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
  items: VisitResponse[];
  total: number;
};

export type AdminClientDetailsData = {
  client: AdminClient;
  services: ServiceItem[];
  appointments: AdminAppointment[];
  visits: VisitResponse[];
};

export type AdminDashboardData = {
  today: DashboardTodayResponse;
  weekGrid: WeekGridResponse;
  analytics: AnalyticsWeekResponse;
  appointments: AdminAppointment[];
};

/** Ответ POST /admin/appointments (без вложенного user). */
export type AppointmentFlat = {
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

export type AdminDataInsightResponse = {
  summary: string;
  sql_executed: string;
  columns: string[];
  rows: Record<string, unknown>[];
  truncated: boolean;
};

export async function postAdminDataInsight(
  token: string,
  question: string,
): Promise<AdminDataInsightResponse> {
  return apiFetch<AdminDataInsightResponse>(
    "/api/v1/admin/analytics/data-insight",
    {
      method: "POST",
      token,
      body: JSON.stringify({ question: question.trim() }),
    },
  );
}

export async function fetchAdminDashboardData(
  token: string,
  weekStart: string = getCurrentWeekStartDateString(),
): Promise<AdminDashboardData> {
  const [today, weekGrid, analytics] = await Promise.all([
    apiFetch<DashboardTodayResponse>("/api/v1/admin/dashboard/today", {
      token,
    }),
    apiFetch<WeekGridResponse>(
      `/api/v1/admin/dashboard/week-grid?week_start=${weekStart}`,
      { token },
    ),
    apiFetch<AnalyticsWeekResponse>(
      `/api/v1/admin/analytics/week?week_start=${weekStart}`,
      { token },
    ),
  ]);
  const weekEnd = addDaysToDateString(weekGrid.week_start, 6);
  const appointments = await apiFetch<AdminAppointmentListResponse>(
    `/api/v1/admin/appointments?date_from=${weekGrid.week_start}&date_to=${weekEnd}&limit=100&offset=0`,
    { token },
  );

  return { today, weekGrid, analytics, appointments: appointments.items };
}

export async function fetchAdminClients(
  token: string,
): Promise<AdminClientListResponse> {
  return apiFetch<AdminClientListResponse>(
    "/api/v1/admin/clients?limit=100&offset=0",
    { token },
  );
}

export async function createAdminClientQuick(
  token: string,
  body: { name: string; phone?: string | null },
): Promise<AdminClient> {
  return apiFetch<AdminClient>("/api/v1/admin/clients", {
    method: "POST",
    token,
    body: JSON.stringify({
      name: body.name.trim(),
      phone: body.phone?.trim() ? body.phone.trim() : null,
    }),
  });
}

export async function createAdminAppointment(
  token: string,
  body: {
    user_id: string;
    starts_at: string;
    service_items: ServiceLineItem[];
    discount_percent: number;
  },
): Promise<AppointmentFlat> {
  return apiFetch<AppointmentFlat>("/api/v1/admin/appointments", {
    method: "POST",
    token,
    body: JSON.stringify(body),
  });
}

export async function fetchAdminClientDetails(
  token: string,
  userId: string,
): Promise<AdminClientDetailsData> {
  const [client, services, appointments, visits] = await Promise.all([
    apiFetch<AdminClient>(`/api/v1/admin/clients/${userId}`, { token }),
    apiFetch<ServiceListResponse>("/api/v1/admin/services?is_active=true", {
      token,
    }),
    apiFetch<AdminAppointmentListResponse>(
      `/api/v1/admin/users/${userId}/appointments?limit=100&offset=0`,
      { token },
    ),
    apiFetch<VisitListResponse>(
      `/api/v1/admin/users/${userId}/visits?limit=100&offset=0`,
      { token },
    ),
  ]);

  return {
    client,
    services: services.items,
    appointments: appointments.items,
    visits: visits.items,
  };
}

export async function cancelAdminAppointment(
  token: string,
  appointmentId: string,
) {
  return apiFetch(`/api/v1/admin/appointments/${appointmentId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ status: "cancelled" }),
  });
}

export async function updateAdminAppointment(
  token: string,
  appointmentId: string,
  body: {
    status?: AppointmentStatus;
    service_items?: ServiceLineItem[];
    discount_percent?: number;
  },
): Promise<AdminAppointment> {
  return apiFetch<AdminAppointment>(`/api/v1/admin/appointments/${appointmentId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(body),
  });
}

export async function confirmAdminVisit(
  token: string,
  appointment: AdminAppointment,
): Promise<VisitResponse> {
  return apiFetch<VisitResponse>("/api/v1/admin/visits", {
    method: "POST",
    token,
    body: JSON.stringify({
      appointment_id: appointment.id,
      lines: appointment.service_items,
      total_amount: appointment.total_price,
      bonus_spent: 0,
    }),
  });
}

export async function updateAdminVisit(
  token: string,
  visitId: string,
  body: {
    lines?: ServiceLineItem[];
    total_amount?: string;
    bonus_spent?: number;
    bonus_earned?: number;
  },
): Promise<VisitResponse> {
  return apiFetch<VisitResponse>(`/api/v1/admin/visits/${visitId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(body),
  });
}

export async function rateAdminVisitClient(
  token: string,
  visitId: string,
  stars: number,
  comment: string,
): Promise<VisitResponse> {
  return apiFetch<VisitResponse>(`/api/v1/admin/visits/${visitId}/client-rating`, {
    method: "POST",
    token,
    body: JSON.stringify({
      stars,
      comment: comment.trim() || null,
    }),
  });
}

export function addDaysToDateString(dateString: string, days: number) {
  const date = new Date(`${dateString}T00:00:00`);
  date.setDate(date.getDate() + days);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

export function getCurrentWeekStartDateString() {
  const date = new Date();
  const day = date.getDay();
  const daysFromMonday = day === 0 ? 6 : day - 1;
  date.setDate(date.getDate() - daysFromMonday);

  return formatDateString(date);
}

function formatDateString(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

