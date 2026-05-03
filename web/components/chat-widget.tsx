"use client";

import {
  BotIcon,
  Loader2Icon,
  MessageCircleIcon,
  MicIcon,
  SendIcon,
  Volume2Icon,
} from "lucide-react";
import {
  type FormEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Sheet,
  SheetContent,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { ApiError, messageFromApiPayload } from "@/lib/api";
import {
  type ConsultationHistoryTurn,
  type ConsultationMessage,
  fetchConsultationMessages,
  postConsultationMessage,
} from "@/lib/consultation-api";
import { loadAuthSession } from "@/lib/auth";
import { cn } from "@/lib/utils";
import {
  cancelSpeechSynthesis,
  createRuSpeechRecognition,
  isBrowserSpeechRecognitionSupported,
  isBrowserSpeechSynthesisSupported,
  speakRussianUtterance,
  speechRecognitionErrorToRuMessage,
  transcribedTextFromResults,
} from "@/lib/web-speech";

const LLM_UNAVAILABLE =
  "Консультант временно недоступен. Попробуйте позже.";
const SEND_FAILED = "Не удалось отправить сообщение. Попробуйте ещё раз.";

function userVisibleSendError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 503) {
      return LLM_UNAVAILABLE;
    }
    if (error.status === 401) {
      return "Сессия недействительна. Выйдите и войдите снова.";
    }
    if (error.status === 422) {
      return messageFromApiPayload(error.details) ?? "Проверьте текст сообщения.";
    }
    if (error.status >= 500) {
      return LLM_UNAVAILABLE;
    }
    return SEND_FAILED;
  }
  return SEND_FAILED;
}

function userVisibleHistoryError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return "Сессия недействительна. Выйдите и войдите снова.";
    }
    return "Не удалось загрузить историю. Закройте панель и откройте снова.";
  }
  return "Не удалось загрузить историю.";
}

function historyPayloadFromMessages(
  messages: ConsultationMessage[],
): ConsultationHistoryTurn[] {
  const tail = messages.slice(-20);
  return tail.map((m) => ({ role: m.role, content: m.content }));
}

const PENDING_USER_ID = "__pending_user__";

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ConsultationMessage[]>([]);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [sendError, setSendError] = useState<string | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [sending, setSending] = useState(false);
  const [pendingText, setPendingText] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [listening, setListening] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<ReturnType<typeof createRuSpeechRecognition>>(null);

  const accessToken = loadAuthSession()?.accessToken ?? null;

  const scrollToBottom = useCallback(() => {
    const el = scrollRef.current;
    if (!el) {
      return;
    }
    queueMicrotask(() => {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    });
  }, []);

  const loadHistory = useCallback(async () => {
    const t = loadAuthSession()?.accessToken;
    if (!t) {
      return;
    }
    setHistoryError(null);
    setLoadingHistory(true);
    try {
      const items = await fetchConsultationMessages(t);
      setMessages(items);
    } catch (e) {
      setHistoryError(userVisibleHistoryError(e));
      setMessages([]);
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  const refreshMessagesSilently = useCallback(async () => {
    const t = loadAuthSession()?.accessToken;
    if (!t) {
      return;
    }
    try {
      const items = await fetchConsultationMessages(t);
      setMessages(items);
    } catch {
      /* не перетираем ленту после успешной отправки */
    }
  }, []);

  const handleSheetOpenChange = useCallback(
    (next: boolean) => {
      if (!next) {
        recognitionRef.current?.abort();
        recognitionRef.current = null;
        setListening(false);
        cancelSpeechSynthesis();
      }
      setOpen(next);
      if (next && loadAuthSession()?.accessToken) {
        void loadHistory();
      }
    },
    [loadHistory],
  );

  const displayMessages: ConsultationMessage[] =
    sending && pendingText
      ? [
          ...messages,
          {
            id: PENDING_USER_ID,
            role: "user",
            content: pendingText,
            created_at: new Date().toISOString(),
            request_id: null,
          },
        ]
      : messages;

  useEffect(() => {
    if (!open) {
      return;
    }
    scrollToBottom();
  }, [open, displayMessages.length, sending, loadingHistory, scrollToBottom]);

  useEffect(() => {
    return () => {
      recognitionRef.current?.abort();
      cancelSpeechSynthesis();
    };
  }, []);

  useEffect(() => {
    if (!open || loadingHistory) {
      return;
    }
    const id = window.setTimeout(() => inputRef.current?.focus(), 50);
    return () => window.clearTimeout(id);
  }, [open, loadingHistory]);

  const stopListening = useCallback(() => {
    try {
      recognitionRef.current?.stop();
    } catch {
      recognitionRef.current?.abort();
    }
    recognitionRef.current = null;
    setListening(false);
  }, []);

  const startListening = useCallback(() => {
    if (listening) {
      stopListening();
      return;
    }
    if (!isBrowserSpeechRecognitionSupported()) {
      setSendError(
        "Распознавание речи в браузере недоступно. Используйте Chrome или Edge по HTTPS или введите текст.",
      );
      return;
    }
    const rec = createRuSpeechRecognition();
    if (!rec) {
      setSendError("Не удалось инициализировать распознавание речи.");
      return;
    }
    setSendError(null);
    rec.onresult = (ev: Event) => {
      const line = transcribedTextFromResults(
        ev as unknown as { results: Iterable<{ 0?: { transcript?: string } }> },
      );
      if (line) {
        setDraft((d) => (d.trim() ? `${d.trim()} ${line}` : line));
      }
      queueMicrotask(() => inputRef.current?.focus());
    };
    rec.onerror = (ev: Event) => {
      const err = (ev as { error?: string }).error ?? "unknown";
      setSendError(speechRecognitionErrorToRuMessage(err));
      setListening(false);
      recognitionRef.current = null;
    };
    rec.onend = () => {
      setListening(false);
      recognitionRef.current = null;
    };
    recognitionRef.current = rec;
    setListening(true);
    try {
      rec.start();
    } catch {
      setListening(false);
      recognitionRef.current = null;
      setSendError("Не удалось начать запись с микрофона.");
    }
  }, [listening, stopListening]);

  const speakLastAssistant = useCallback(() => {
    const last = [...messages].reverse().find((m) => m.role === "assistant");
    const content = last?.content?.trim();
    if (!content) {
      setSendError("Пока нет ответа ассистента для озвучивания.");
      return;
    }
    if (!isBrowserSpeechSynthesisSupported()) {
      setSendError("Озвучивание в этом браузере не поддерживается.");
      return;
    }
    setSendError(null);
    speakRussianUtterance(content);
  }, [messages]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = draft.trim();
    const t = loadAuthSession()?.accessToken;
    if (!text || !t || sending) {
      return;
    }

    setSendError(null);
    setSending(true);
    setPendingText(text);
    const history = historyPayloadFromMessages(messages);
    setDraft("");

    try {
      await postConsultationMessage(t, text, history);
      await refreshMessagesSilently();
    } catch (e) {
      setDraft(text);
      setSendError(userVisibleSendError(e));
    } finally {
      setSending(false);
      setPendingText(null);
    }
  }

  const voiceBusy = listening || sending || loadingHistory || !accessToken;

  return (
    <Sheet open={open} onOpenChange={handleSheetOpenChange}>
      <SheetTrigger
        render={
          <Button
            size="lg"
            className="fixed right-6 bottom-6 z-40 rounded-full bg-zinc-900 text-zinc-50 shadow-lg hover:bg-zinc-800 dark:bg-emerald-700 dark:hover:bg-emerald-600"
          />
        }
      >
        <MessageCircleIcon data-icon="inline-start" />
        Чат
      </SheetTrigger>
      <SheetContent
        showCloseButton
        className="flex h-[100dvh] max-h-[100dvh] w-full flex-col gap-0 border-zinc-800 bg-zinc-950 p-0 text-zinc-100 sm:max-w-md"
      >
        <SheetHeader className="shrink-0 border-b border-zinc-800 px-4 pt-6 pb-4">
          <SheetTitle className="text-zinc-100">AI-ассистент</SheetTitle>
        </SheetHeader>

        <div
          ref={scrollRef}
          className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto px-4 py-3"
          role="log"
          aria-live="polite"
          aria-relevant="additions"
        >
          {loadingHistory ? (
            <div className="flex flex-1 items-center justify-center gap-2 text-sm text-zinc-400">
              <Loader2Icon className="size-5 animate-spin" aria-hidden />
              Загрузка истории…
            </div>
          ) : null}

          {!loadingHistory && historyError ? (
            <p className="rounded-lg border border-amber-900/80 bg-amber-950/40 px-3 py-2 text-sm text-amber-100">
              {historyError}
            </p>
          ) : null}

          {!loadingHistory &&
            displayMessages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "flex w-full gap-2",
                  message.role === "user" ? "justify-end" : "justify-start",
                )}
              >
                {message.role === "assistant" ? (
                  <div
                    className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-md bg-emerald-900/60 text-emerald-300"
                    aria-hidden
                  >
                    <BotIcon className="size-4" />
                  </div>
                ) : (
                  <span className="sr-only">Вы:</span>
                )}
                <div
                  className={cn(
                    "max-w-[85%] rounded-lg px-3 py-2 text-sm leading-relaxed wrap-break-word whitespace-pre-wrap",
                    message.role === "user"
                      ? "bg-emerald-700 text-white"
                      : "border border-zinc-700 bg-zinc-900 text-zinc-100",
                    message.id === PENDING_USER_ID && "opacity-90",
                  )}
                >
                  {message.id === PENDING_USER_ID && sending ? (
                    <span className="inline-flex items-center gap-2">
                      {message.content}
                      <Loader2Icon
                        className="size-3.5 shrink-0 animate-spin opacity-80"
                        aria-hidden
                      />
                    </span>
                  ) : (
                    message.content
                  )}
                </div>
              </div>
            ))}
        </div>

        <SheetFooter className="shrink-0 border-t border-zinc-800 bg-zinc-950 px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pt-3">
          {listening ? (
            <p className="mb-2 flex items-center gap-2 text-sm text-zinc-400">
              <span className="inline-block size-2 animate-pulse rounded-full bg-emerald-500" />
              Слушаю… скажите фразу и сделайте паузу.
            </p>
          ) : null}
          {sendError ? (
            <p className="mb-2 text-sm text-red-400">{sendError}</p>
          ) : null}
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              ref={inputRef}
              aria-label="Сообщение ассистенту"
              placeholder="Напишите вопрос…"
              value={draft}
              disabled={sending || loadingHistory || !accessToken}
              onChange={(e) => setDraft(e.target.value)}
              className="border-zinc-700 bg-zinc-900 text-zinc-100 placeholder:text-zinc-500"
            />
            <Button
              type="button"
              size="icon"
              variant="secondary"
              disabled={voiceBusy}
              onClick={startListening}
              aria-pressed={listening}
              aria-label={
                listening ? "Остановить запись с микрофона" : "Голосовой ввод"
              }
              className="shrink-0 border-zinc-700 bg-zinc-900 text-zinc-100 hover:bg-zinc-800"
            >
              {listening ? (
                <Loader2Icon className="size-4 animate-spin" aria-hidden />
              ) : (
                <MicIcon className="size-4" aria-hidden />
              )}
            </Button>
            <Button
              type="button"
              size="icon"
              variant="secondary"
              disabled={loadingHistory || !accessToken}
              onClick={speakLastAssistant}
              aria-label="Озвучить последний ответ ассистента"
              className="shrink-0 border-zinc-700 bg-zinc-900 text-zinc-100 hover:bg-zinc-800"
            >
              <Volume2Icon className="size-4" aria-hidden />
            </Button>
            <Button
              type="submit"
              size="icon"
              disabled={
                sending || loadingHistory || !draft.trim() || !accessToken
              }
              aria-label="Отправить сообщение"
              className="shrink-0 bg-emerald-700 hover:bg-emerald-600"
            >
              {sending ? (
                <Loader2Icon className="size-4 animate-spin" />
              ) : (
                <SendIcon />
              )}
            </Button>
          </form>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
