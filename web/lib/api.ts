export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Сообщение для пользователя из тела ответа FastAPI / обёрток. */
export function messageFromApiPayload(payload: unknown): string | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }
  const rec = payload as Record<string, unknown>;

  /** Контракт «Переобуйка»: HTTPException → JSON без `detail`, сразу `{ error: { code, message } }`. */
  const topError = rec.error;
  if (topError && typeof topError === "object") {
    const e = topError as Record<string, unknown>;
    if (typeof e.message === "string") {
      return e.message;
    }
  }

  const detail = rec.detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (detail && typeof detail === "object") {
    const d = detail as Record<string, unknown>;
    if (typeof d.message === "string") {
      return d.message;
    }
    const err = d.error;
    if (err && typeof err === "object") {
      const e = err as Record<string, unknown>;
      if (typeof e.message === "string") {
        return e.message;
      }
    }
  }
  if (typeof rec.message === "string") {
    return rec.message;
  }
  return null;
}

/** На Windows `localhost` часто резолвится в IPv6 (::1), а uvicorn по умолчанию слушает только 127.0.0.1. */
const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

/** Убираем хвост `/api/v1`: пути в клиенте уже начинаются с `/api/v1/...`, иначе получится двойной префикс и ответ 404. */
function normalizeApiOrigin(raw: string): string {
  let base = raw.trim().replace(/\/+$/, "");
  const suffix = "/api/v1";
  if (base.toLowerCase().endsWith(suffix)) {
    base = base.slice(0, -suffix.length).replace(/\/+$/, "");
  }
  return base || DEFAULT_API_BASE_URL;
}

export function getApiBaseUrl() {
  const fromEnv = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  return normalizeApiOrigin(fromEnv && fromEnv.length > 0 ? fromEnv : DEFAULT_API_BASE_URL);
}

type ApiFetchOptions = RequestInit & {
  token?: string;
};

export async function apiFetch<T>(
  path: string,
  { token, headers, ...init }: ApiFetchOptions = {},
): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  const contentType = response.headers.get("content-type");
  const payload = contentType?.includes("application/json")
    ? await response.json()
    : null;

  if (!response.ok) {
    const parsed = messageFromApiPayload(payload);
    const message =
      parsed ?? "Backend вернул ошибку запроса.";

    throw new ApiError(message, response.status, payload);
  }

  return payload as T;
}

