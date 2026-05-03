"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { LayoutDashboardIcon, LogOutIcon, UsersRoundIcon } from "lucide-react";

import { ChatWidget } from "@/components/chat-widget";
import { LoginForm } from "@/components/auth/login-form";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  clearAuthSession,
  loadAuthSession,
  type AuthSession,
  type UserRole,
} from "@/lib/auth";
import { TooltipProvider } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

type AppShellProps = {
  children: React.ReactNode;
};

const ADMIN_NAV = [
  {
    href: "/admin",
    label: "Панель администратора",
    icon: LayoutDashboardIcon,
  },
  {
    href: "/admin/clients",
    label: "Клиенты",
    icon: UsersRoundIcon,
  },
] satisfies Array<{
  href: string;
  label: string;
  icon: typeof LayoutDashboardIcon;
}>;

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [session, setSession] = useState<AuthSession | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    queueMicrotask(() => {
      setSession(loadAuthSession());
      setIsReady(true);
    });
  }, []);

  function handleLogin(nextSession: AuthSession) {
    setSession(nextSession);
    router.push(nextSession.user.role === "admin" ? "/admin" : "/client");
  }

  function handleLogout() {
    clearAuthSession();
    setSession(null);
    router.push("/");
  }

  if (!isReady) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-muted p-6">
        <Card className="w-full max-w-sm">
          <CardHeader>
            <CardTitle>Переобуйка Web</CardTitle>
            <CardDescription>Загружаем локальную сессию...</CardDescription>
          </CardHeader>
        </Card>
      </main>
    );
  }

  if (!session) {
    return <LoginForm onLogin={handleLogin} />;
  }

  const isAdminRoute = pathname.startsWith("/admin");
  const isClientRoute = pathname.startsWith("/client");
  const isForbidden =
    (isAdminRoute && session.user.role !== "admin") ||
    (isClientRoute && session.user.role !== "client");

  const role: UserRole = session.user.role;
  const homeHref = role === "admin" ? "/admin" : "/client";

  return (
    <TooltipProvider delay={200}>
      <div className="min-h-screen bg-muted">
        <div className="mx-auto flex min-h-screen w-full max-w-screen-2xl flex-col">
          <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
            <div className="flex flex-col gap-0 px-4 py-3 lg:px-8">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex min-w-0 flex-wrap items-center gap-x-4 gap-y-1">
                  <Link
                    href={homeHref}
                    className="shrink-0 text-lg font-semibold text-foreground transition-colors hover:text-primary"
                  >
                    Переобуйка
                  </Link>
                  <div className="hidden h-4 w-px shrink-0 bg-border sm:block" />
                  <div className="min-w-0">
                    <p className="truncate text-xs text-muted-foreground sm:text-sm">
                      {role === "admin"
                        ? "Административный контур"
                        : "Личный кабинет"}
                    </p>
                    <h1 className="truncate text-base font-semibold sm:text-lg">
                      {session.user.name}
                    </h1>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2 sm:gap-3">
                  {role === "admin" ? (
                    <Badge variant="outline" className="hidden sm:inline-flex">
                      Админ
                    </Badge>
                  ) : null}
                  <Avatar>
                    <AvatarFallback>
                      {session.user.name.slice(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <Button variant="outline" size="sm" onClick={handleLogout}>
                    <LogOutIcon data-icon="inline-start" />
                    Выйти
                  </Button>
                </div>
              </div>

              {role === "admin" ? (
                <nav
                  aria-label="Разделы администратора"
                  className="mt-3 flex gap-1 overflow-x-auto border-t pt-3 [scrollbar-width:thin]"
                >
                  {ADMIN_NAV.map((item) => {
                    const Icon = item.icon;
                    const isActive = pathname === item.href;

                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        className={cn(
                          "inline-flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                          isActive
                            ? "bg-accent text-accent-foreground"
                            : "text-muted-foreground hover:bg-muted hover:text-foreground",
                        )}
                      >
                        <Icon aria-hidden="true" />
                        {item.label}
                      </Link>
                    );
                  })}
                </nav>
              ) : null}
            </div>
          </header>

          <main className="flex-1 p-4 lg:p-8">
            {isForbidden ? (
              <Card>
                <CardHeader>
                  <CardTitle>Нет доступа к разделу</CardTitle>
                  <CardDescription>
                    Текущая роль не совпадает с ролью маршрута.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button
                    type="button"
                    onClick={() =>
                      router.push(
                        session.user.role === "admin" ? "/admin" : "/client",
                      )
                    }
                  >
                    Вернуться в свой раздел
                  </Button>
                </CardContent>
              </Card>
            ) : (
              children
            )}
          </main>
        </div>
        {role === "client" ? <ChatWidget /> : null}
      </div>
    </TooltipProvider>
  );
}
