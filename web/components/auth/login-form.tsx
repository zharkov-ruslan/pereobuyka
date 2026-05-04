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
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { ThemeToggle } from "@/components/theme-toggle";

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
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle>Переобуйка Web</CardTitle>
            <ThemeToggle />
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
                <FieldLabel htmlFor="admin-token">Токен администратора</FieldLabel>
                <Input
                  id="admin-token"
                  type="password"
                  placeholder="••••••••"
                  value={adminToken}
                  onChange={(event) => setAdminToken(event.target.value)}
                  autoComplete="off"
                />
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

