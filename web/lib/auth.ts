export type UserRole = "admin" | "client";

export type WebUser = {
  id: string;
  name: string;
  phone: string | null;
  role: UserRole;
  telegram_id: number | null;
  telegram_username: string | null;
  registered_at: string;
  source: string;
};

export type AuthSession = {
  accessToken: string;
  tokenType: string;
  user: WebUser;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  user: WebUser;
};

export type WebAuthRequest = {
  telegram_username: string;
  name?: string;
  phone?: string;
};

const AUTH_STORAGE_KEY = "pereobuyka:web:auth";

export function toAuthSession(response: TokenResponse): AuthSession {
  return {
    accessToken: response.access_token,
    tokenType: response.token_type,
    user: response.user,
  };
}

export function loadAuthSession(): AuthSession | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as AuthSession;
  } catch {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
    return null;
  }
}

export function saveAuthSession(session: AuthSession) {
  window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
}

export function clearAuthSession() {
  window.localStorage.removeItem(AUTH_STORAGE_KEY);
}

export function createManualAdminSession(token: string): AuthSession {
  return {
    accessToken: token,
    tokenType: "bearer",
    user: {
      id: "manual-admin",
      name: "Администратор",
      phone: null,
      role: "admin",
      telegram_id: null,
      telegram_username: null,
      registered_at: new Date().toISOString(),
      source: "web",
    },
  };
}

