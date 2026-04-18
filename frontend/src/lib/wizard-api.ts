import type {
  WizardSession,
  EmojiStyle,
  ImageProvider,
  Tier,
  WizardStep,
  EmojiResult,
  PetFeatures,
} from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** 위자드 세션 시작 */
export async function wizardStart(
  file: File,
  tier: Tier,
  provider: ImageProvider,
): Promise<WizardSession> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("tier", tier);
  formData.append("provider", provider);
  formData.append("analyzer", "gemini");

  const res = await fetch(`${API_BASE}/api/wizard/start`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`세션 시작 실패 (${res.status}): ${text}`);
  }

  return res.json();
}

/** 위자드 단계 실행 (SSE) */
export function wizardStep(
  sessionId: string,
  sessionToken: string,
  step: WizardStep,
  selection: Record<string, unknown>,
  callbacks: {
    onProgress: (data: { step: string; message: string; progress: number }) => void;
    onPreview: (data: { step: string; image_url: string }) => void;
    onError: (error: Error) => void;
  }
): AbortController {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${API_BASE}/api/wizard/step`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-Token": sessionToken,
        },
        body: JSON.stringify({ session_id: sessionId, step, selection }),
        signal: controller.signal,
      });

      if (!res.ok) throw new Error(`단계 실행 실패 (${res.status})`);

      const reader = res.body?.getReader();
      if (!reader) throw new Error("스트리밍 불가");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const events = buffer.split("\n\n");
        buffer = events.pop() || "";

        for (const eventStr of events) {
          if (!eventStr.trim()) continue;
          let eventType = "";
          let eventData = "";
          for (const line of eventStr.split("\n")) {
            if (line.startsWith("event: ")) eventType = line.slice(7);
            else if (line.startsWith("data: ")) eventData = line.slice(6);
          }
          if (!eventType || !eventData) continue;
          const data = JSON.parse(eventData);

          if (eventType === "progress") callbacks.onProgress(data);
          else if (eventType === "preview") callbacks.onPreview(data);
          else if (eventType === "error") callbacks.onError(new Error(data.message));
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        callbacks.onError(err instanceof Error ? err : new Error("알 수 없는 오류"));
      }
    }
  })();

  return controller;
}

/** 뒤로 가기 */
export async function wizardBack(
  sessionId: string,
  sessionToken: string,
  targetStep: WizardStep
): Promise<{ current_step: string; previews: Record<string, string> }> {
  const res = await fetch(`${API_BASE}/api/wizard/back`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Session-Token": sessionToken,
    },
    body: JSON.stringify({ session_id: sessionId, target_step: targetStep }),
  });

  if (!res.ok) throw new Error("뒤로 가기 실패");
  return res.json();
}

/** 이모지 세트 생성 (SSE) */
export function wizardGenerate(
  sessionId: string,
  sessionToken: string,
  emojiCount: number,
  callbacks: {
    onProgress: (data: { step: string; message: string; progress: number }) => void;
    onEmoji: (data: { emotion: string; image_url: string; index: number; total: number }) => void;
    onComplete: (data: { pet_features: PetFeatures; emojis: EmojiResult[] }) => void;
    onError: (error: Error) => void;
  }
): AbortController {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${API_BASE}/api/wizard/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-Token": sessionToken,
        },
        body: JSON.stringify({ session_id: sessionId, emoji_count: emojiCount }),
        signal: controller.signal,
      });

      if (!res.ok) throw new Error(`생성 실패 (${res.status})`);

      const reader = res.body?.getReader();
      if (!reader) throw new Error("스트리밍 불가");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const events = buffer.split("\n\n");
        buffer = events.pop() || "";

        for (const eventStr of events) {
          if (!eventStr.trim()) continue;
          let eventType = "";
          let eventData = "";
          for (const line of eventStr.split("\n")) {
            if (line.startsWith("event: ")) eventType = line.slice(7);
            else if (line.startsWith("data: ")) eventData = line.slice(6);
          }
          if (!eventType || !eventData) continue;
          const data = JSON.parse(eventData);

          if (eventType === "progress") callbacks.onProgress(data);
          else if (eventType === "emoji") callbacks.onEmoji(data);
          else if (eventType === "complete") callbacks.onComplete(data);
          else if (eventType === "error") callbacks.onError(new Error(data.message));
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        callbacks.onError(err instanceof Error ? err : new Error("알 수 없는 오류"));
      }
    }
  })();

  return controller;
}
