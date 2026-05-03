import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function Home() {
  return (
    <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex flex-col gap-2">
              <CardTitle>Каркас веб-приложения готов</CardTitle>
              <CardDescription>
                Это стартовый экран после входа. Рабочие разделы будут
                наполняться в следующих итерациях.
              </CardDescription>
            </div>
            <Badge variant="secondary">Next.js App Router</Badge>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">
            Бизнес-расчёты остаются в backend: frontend вызывает API, хранит
            только локальную MVP-сессию и отображает состояния экранов.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link href="/client" className={buttonVariants()}>
              Личный кабинет
            </Link>
            <Link
              href="/admin"
              className={buttonVariants({ variant: "outline" })}
            >
              Панель администратора
            </Link>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Что внутри</CardTitle>
          <CardDescription>
            Базовые соглашения, на которые будут опираться iter-fe-03+.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="flex flex-col gap-2 text-sm text-muted-foreground">
            <li>shadcn/ui + Tailwind v4 токены темы.</li>
            <li>Единый API-клиент с `NEXT_PUBLIC_API_BASE_URL`.</li>
            <li>Роль-зависимая навигация и выход из локальной сессии.</li>
            <li>Глобальная оболочка чат-виджета.</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
