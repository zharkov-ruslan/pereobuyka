"use client";

import { useEffect, useState } from "react";

import { AdminDataInsightCard } from "@/components/admin-data-insight-card";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { loadAuthSession } from "@/lib/auth";

export default function AdminAnalyticsPage() {
  const [token, setToken] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    queueMicrotask(() => {
      const session = loadAuthSession();
      if (!session || session.user.role !== "admin") {
        setToken(null);
      } else {
        setToken(session.accessToken);
      }
      setReady(true);
    });
  }, []);

  if (!ready) {
    return null;
  }

  if (!token) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Сессия не найдена</CardTitle>
          <CardDescription>
            Зайдите как администратор, чтобы задавать вопросы к данным.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <AdminDataInsightCard token={token} />
    </div>
  );
}
