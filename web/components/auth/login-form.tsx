"use client";

import { FormEvent, useState } from "react";
import { KeyRoundIcon, LogInIcon } from "lucide-react";

import { apiFetch } from "@/lib/api";
import {
  createManualAdminSession,
  saveAuthSession,
  toAuthSession,
  type AuthSession,
  type TokenResponse,
  type WebAuthRequest,
} from "@/lib/auth";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
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
import { Separator } from "@/components/ui/separator";

type LoginFormProps = {
  onLogin: (session: AuthSession) => void;
};

export function LoginForm({ onLogin }: LoginFormProps) {
  const [telegramUsername, setTelegramUsername] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [adminToken, setAdminToken] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);

  async function handleClientLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsPending(true);

    const body: WebAuthRequest = {
      telegram_username: telegramUsername.trim(),
      ...(name.trim() ? { name: name.trim() } : {}),
      ...(phone.trim() ? { phone: phone.trim() } : {}),
    };

    try {
      const token = await apiFetch<TokenResponse>("/api/v1/auth/web", {
        method: "POST",
        body: JSON.stringify(body),
      });
      const session = toAuthSession(token);
      saveAuthSession(session);
      onLogin(session);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Не удалось выполнить вход.",
      );
    } finally {
      setIsPending(false);
    }
  }

  function handleAdminLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const token = adminToken.trim();
    if (!token) {
      setError("Вставьте Bearer token администратора.");
      return;
    }

    const session = createManualAdminSession(token);
    saveAuthSession(session);
    onLogin(session);
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-muted p-6">
      <Card className="w-full max-w-5xl">
        <CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex flex-col gap-2">
              <CardTitle>Переобуйка Web</CardTitle>
              <CardDescription>
                MVP-вход для клиента и ручной админ-доступ для локальной демо.
              </CardDescription>
            </div>
            <Badge variant="secondary">iter-fe-02</Badge>
          </div>
        </CardHeader>
        <CardContent className="grid gap-6 lg:grid-cols-[1fr_auto_1fr]">
          <form onSubmit={handleClientLogin}>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="telegram-username">
                  Telegram username
                </FieldLabel>
                <Input
                  id="telegram-username"
                  placeholder="@ivan"
                  value={telegramUsername}
                  onChange={(event) => setTelegramUsername(event.target.value)}
                  required
                />
                <FieldDescription>
                  Backend вызовет `POST /api/v1/auth/web` и вернёт JWT клиента.
                </FieldDescription>
              </Field>
              <Field>
                <FieldLabel htmlFor="client-name">Имя</FieldLabel>
                <Input
                  id="client-name"
                  placeholder="Иван"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="client-phone">Телефон</FieldLabel>
                <Input
                  id="client-phone"
                  placeholder="+7..."
                  value={phone}
                  onChange={(event) => setPhone(event.target.value)}
                />
              </Field>
              <Field>
                <Button type="submit" disabled={isPending}>
                  <LogInIcon data-icon="inline-start" />
                  {isPending ? "Входим..." : "Войти как клиент"}
                </Button>
              </Field>
            </FieldGroup>
          </form>

          <Separator orientation="vertical" className="hidden lg:block" />
          <Separator className="lg:hidden" />

          <form onSubmit={handleAdminLogin}>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="admin-token">
                  Секрет админ-панели (ADMIN_API_TOKEN)
                </FieldLabel>
                <Input
                  id="admin-token"
                  placeholder="Значение из backend/.env → ADMIN_API_TOKEN"
                  value={adminToken}
                  onChange={(event) => setAdminToken(event.target.value)}
                  autoComplete="off"
                />
                <FieldDescription>
                  Для запросов к /api/v1/admin/* backend сверяет Bearer с переменной{" "}
                  <code className="rounded bg-muted px-1 py-0.5 text-xs">
                    ADMIN_API_TOKEN
                  </code>
                  , а не с токеном{" "}
                  <code className="rounded bg-muted px-1 py-0.5 text-xs">
                    mvp-…
                  </code>{" "}
                  клиента.
                </FieldDescription>
              </Field>
              <Field>
                <Button type="submit" variant="outline">
                  <KeyRoundIcon data-icon="inline-start" />
                  Войти как администратор
                </Button>
              </Field>
            </FieldGroup>
          </form>
        </CardContent>
        {error ? (
          <CardFooter>
            <p className="text-sm text-destructive">{error}</p>
          </CardFooter>
        ) : null}
      </Card>
    </main>
  );
}

