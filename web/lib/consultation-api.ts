import { apiFetch } from "@/lib/api";

export type ConsultationMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  request_id: string | null;
};

type ConsultationMessageListResponse = {
  items: ConsultationMessage[];
  total: number;
};

type ConsultationPostResponse = {
  reply: string;
  request_id: string | null;
};

export type ConsultationHistoryTurn = {
  role: "user" | "assistant";
  content: string;
};

const PAGE = 100;

/** Вся история для текущего пользователя (несколько страниц при total > 100). */
export async function fetchConsultationMessages(
  token: string,
): Promise<ConsultationMessage[]> {
  const all: ConsultationMessage[] = [];
  let offset = 0;

  for (;;) {
    const res = await apiFetch<ConsultationMessageListResponse>(
      `/api/v1/consultation/messages?limit=${PAGE}&offset=${offset}`,
      { token },
    );
    all.push(...res.items);
    if (all.length >= res.total || res.items.length === 0) {
      break;
    }
    offset += PAGE;
  }

  return all;
}

export async function postConsultationMessage(
  token: string,
  message: string,
  history: ConsultationHistoryTurn[],
): Promise<ConsultationPostResponse> {
  return apiFetch<ConsultationPostResponse>("/api/v1/consultation/messages", {
    method: "POST",
    body: JSON.stringify({ message, history }),
    token,
  });
}
