/** Web Speech API: распознавание (STT) и озвучивание (TTS) для чата. Без записи сырого аудио в логи приложения. */

/** Минимальный тип для остановки/прерывания без зависимости от DOM-либы TS. */
export type SpeechRecognitionHandle = {
  start: () => void;
  stop: () => void;
  abort: () => void;
};

export function isBrowserSpeechRecognitionSupported(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  const w = window as unknown as {
    SpeechRecognition?: new () => SpeechRecognitionHandle & Record<string, unknown>;
    webkitSpeechRecognition?: new () => SpeechRecognitionHandle & Record<string, unknown>;
  };
  return Boolean(w.SpeechRecognition ?? w.webkitSpeechRecognition);
}

export function isBrowserSpeechSynthesisSupported(): boolean {
  return typeof window !== "undefined" && Boolean(window.speechSynthesis);
}

/** Создать экземпляр распознавателя с ru-RU или null, если API нет. */
export function createRuSpeechRecognition(): (SpeechRecognitionHandle & {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((ev: Event) => void) | null;
  onerror: ((ev: Event) => void) | null;
  onend: (() => void) | null;
}) | null {
  if (typeof window === "undefined") {
    return null;
  }
  const w = window as unknown as {
    SpeechRecognition?: new () => SpeechRecognitionHandle & {
      lang: string;
      continuous: boolean;
      interimResults: boolean;
      onresult: ((ev: Event) => void) | null;
      onerror: ((ev: Event) => void) | null;
      onend: (() => void) | null;
    };
    webkitSpeechRecognition?: new () => SpeechRecognitionHandle & {
      lang: string;
      continuous: boolean;
      interimResults: boolean;
      onresult: ((ev: Event) => void) | null;
      onerror: ((ev: Event) => void) | null;
      onend: (() => void) | null;
    };
  };
  const Ctor = w.SpeechRecognition ?? w.webkitSpeechRecognition;
  if (!Ctor) {
    return null;
  }
  const r = new Ctor();
  r.lang = "ru-RU";
  r.continuous = false;
  r.interimResults = false;
  return r;
}

export function speechRecognitionErrorToRuMessage(code: string): string {
  switch (code) {
    case "not-allowed":
    case "service-not-allowed":
      return "Нет доступа к микрофону. Разрешите запись в настройках сайта или браузера.";
    case "no-speech":
      return "Речь не распознана. Повторите ближе к микрофону.";
    case "audio-capture":
      return "Микрофон недоступен. Проверьте устройство.";
    case "network":
      return "Ошибка сети при распознавании. Проверьте подключение.";
    case "aborted":
      return "Распознавание прервано.";
    default:
      return "Не удалось распознать речь в браузере.";
  }
}

export function speakRussianUtterance(text: string): void {
  const t = text.trim();
  if (!t || typeof window === "undefined" || !window.speechSynthesis) {
    return;
  }
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(t);
  u.lang = "ru-RU";
  window.speechSynthesis.speak(u);
}

export function cancelSpeechSynthesis(): void {
  if (typeof window !== "undefined" && window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
}

export function transcribedTextFromResults(ev: {
  results: Iterable<{ 0?: { transcript?: string } | undefined }>;
}): string {
  return Array.from(ev.results)
    .map((r) => (r[0]?.transcript ?? "").trim())
    .join(" ")
    .trim();
}
