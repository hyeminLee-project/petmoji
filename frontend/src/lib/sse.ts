import type { EmojiStyle, ImageProvider, PetFeatures, EmojiResult } from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ProgressEvent {
  step: "analyzing" | "analyzed" | "captioning" | "generating" | "complete";
  message: string;
  progress: number;
  current?: number;
  total?: number;
  pet_features?: PetFeatures;
}

export interface EmojiEvent {
  emotion: string;
  image_url: string;
  index: number;
  total: number;
}

interface StreamCallbacks {
  onProgress: (event: ProgressEvent) => void;
  onEmoji: (emoji: EmojiEvent) => void;
  onComplete: (data: { pet_features: PetFeatures; emojis: EmojiResult[] }) => void;
  onError: (error: Error) => void;
}

/**
 * SSE 기반 이모지 생성 스트리밍
 * @returns AbortController (취소용)
 */
export function generateEmojisStream(
  file: File,
  style: EmojiStyle,
  emojiCount: number,
  provider: ImageProvider,
  customPrompt: string,
  callbacks: StreamCallbacks,
): AbortController {
  const controller = new AbortController();

  const formData = new FormData();
  formData.append("file", file);
  formData.append("style", style);
  formData.append("emoji_count", String(emojiCount));
  formData.append("provider", provider);
  formData.append("custom_prompt", customPrompt);

  (async () => {
    try {
      const res = await fetch(`${API_BASE}/api/generate/stream`, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });

      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(`서버 오류 (${res.status}): ${text || "알 수 없는 오류"}`);
      }

      const reader = res.body?.getReader();
      if (!reader) throw new Error("스트리밍을 지원하지 않는 응답입니다");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // SSE 이벤트 파싱 (더블 뉴라인으로 구분)
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";

        for (const eventStr of events) {
          if (!eventStr.trim()) continue;

          let eventType = "";
          let eventData = "";

          for (const line of eventStr.split("\n")) {
            if (line.startsWith("event: ")) {
              eventType = line.slice(7);
            } else if (line.startsWith("data: ")) {
              eventData = line.slice(6);
            }
          }

          if (!eventType || !eventData) continue;

          const data = JSON.parse(eventData);

          switch (eventType) {
            case "progress":
              callbacks.onProgress(data as ProgressEvent);
              break;
            case "emoji":
              callbacks.onEmoji(data as EmojiEvent);
              break;
            case "complete":
              callbacks.onComplete(data);
              break;
            case "error":
              callbacks.onError(new Error(data.message));
              break;
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        callbacks.onError(
          err instanceof Error ? err : new Error("스트리밍 연결에 실패했습니다")
        );
      }
    }
  })();

  return controller;
}
