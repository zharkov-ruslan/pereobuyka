"use client";

import { useState, useTransition } from "react";
import { DatabaseIcon } from "lucide-react";

import { ApiError } from "@/lib/api";
import {
  postAdminDataInsight,
  type AdminDataInsightResponse,
} from "@/lib/admin-api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import { cn } from "@/lib/utils";

type AdminDataInsightCardProps = {
  token: string;
};

export function AdminDataInsightCard({ token }: AdminDataInsightCardProps) {
  const [nlQuestion, setNlQuestion] = useState("");
  const [nlError, setNlError] = useState<string | null>(null);
  const [nlResult, setNlResult] = useState<AdminDataInsightResponse | null>(
    null,
  );
  const [isPending, startTransition] = useTransition();

  function handleSubmit() {
    if (!nlQuestion.trim()) {
      return;
    }
    startTransition(async () => {
      setNlError(null);
      setNlResult(null);
      try {
        setNlResult(await postAdminDataInsight(token, nlQuestion));
      } catch (currentError) {
        setNlError(getErrorMessage(currentError));
      }
    });
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <DatabaseIcon className="h-5 w-5 shrink-0" aria-hidden />
          Вопрос к данным
        </CardTitle>
        <CardDescription>
          Коротко опишите, что посчитать или найти по клиентам, записям и визитам.
          Выполняется только безопасное чтение (SELECT с ограничениями); нужен ключ
          LLM на сервере.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <FieldGroup className="gap-2">
          <Field>
            <FieldLabel htmlFor="admin-nl-sql">Формулировка</FieldLabel>
            <textarea
              id="admin-nl-sql"
              rows={3}
              value={nlQuestion}
              onChange={(event) => setNlQuestion(event.target.value)}
              disabled={isPending}
              placeholder='Например: сколько пользователей с ролью "client"?'
              className={cn(
                "min-h-[5rem] w-full resize-y rounded-lg border border-input bg-transparent px-2.5 py-2 text-sm transition-colors outline-none",
                "placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50",
                "disabled:pointer-events-none disabled:opacity-50 dark:bg-input/30",
              )}
            />
          </Field>
        </FieldGroup>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            disabled={isPending || !nlQuestion.trim()}
            onClick={handleSubmit}
          >
            {isPending ? "Запрос…" : "Отправить"}
          </Button>
          {nlResult?.truncated ? (
            <Badge variant="secondary">Строки обрезаны по лимиту</Badge>
          ) : null}
        </div>
        {nlError ? (
          <p className="text-sm text-destructive" role="alert">
            {nlError}
          </p>
        ) : null}
        {nlResult ? (
          <div className="flex flex-col gap-3 text-sm">
            <div>
              <p className="font-medium text-foreground">Ответ</p>
              <p className="mt-1 whitespace-pre-wrap text-muted-foreground">
                {nlResult.summary}
              </p>
            </div>
            <details className="rounded-lg border border-border bg-muted/40 px-3 py-2">
              <summary className="cursor-pointer text-xs font-medium">
                Показать SQL
              </summary>
              <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-all text-xs">
                {nlResult.sql_executed}
              </pre>
            </details>
            {nlResult.rows.length > 0 ? (
              <div className="overflow-auto rounded-lg border border-border">
                <table className="w-full min-w-[280px] border-collapse text-xs">
                  <thead className="bg-muted/60">
                    <tr>
                      {nlResult.columns.map((column) => (
                        <th
                          key={column}
                          className="border-b border-border px-2 py-1.5 text-left font-medium"
                        >
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {nlResult.rows.slice(0, 20).map((row, rowIndex) => (
                      <tr
                        key={rowIndex}
                        className="odd:bg-background even:bg-muted/25"
                      >
                        {nlResult.columns.map((column) => (
                          <td
                            key={`${rowIndex}-${column}`}
                            className="border-b border-border px-2 py-1.5 align-top"
                          >
                            {formatNlPreviewCell(row[column])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function formatNlPreviewCell(value: unknown): string {
  if (value === null || value === undefined) {
    return "—";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Неизвестная ошибка.";
}
