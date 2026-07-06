import type { EmojiStyle, ImageProvider, PetFeatures, EmojiResult } from "@/types/api";
import { readSSEStream } from "./sse-parser";

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
  caption?: string;
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

      await readSSEStream(res, (eventType, data) => {
        switch (eventType) {
          case "progress":
            callbacks.onProgress(data as ProgressEvent);
            break;
          case "emoji":
            callbacks.onEmoji(data as EmojiEvent);
            break;
          case "complete":
            callbacks.onComplete(data as { pet_features: PetFeatures; emojis: EmojiResult[] });
            break;
          case "error":
            callbacks.onError(new Error((data as { message: string }).message));
            break;
        }
      });
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
