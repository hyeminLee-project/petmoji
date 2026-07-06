"use client";

import { useCallback, useState } from "react";
import type { EmojiResult, GenerateResponse, WizardSession } from "@/types/api";
import { wizardGenerate } from "@/lib/wizard-api";

/** 이모지 세트 생성 상태 관리 — SSE 스트리밍 수신, 부분 결과, 완료/에러 */
export function useWizardGenerate(session: WizardSession) {
  const [generating, setGenerating] = useState(false);
  const [partialEmojis, setPartialEmojis] = useState<EmojiResult[]>([]);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);

  const generate = useCallback(() => {
    setGenerating(true);
    setPartialEmojis([]);
    setError(null);

    const maxEmotions = session.tier_config.max_emotions || 8;

    wizardGenerate(session.session_id, session.session_token, maxEmotions, {
      onProgress: (data) => setMessage(data.message),
      onEmoji: (data) => {
        setPartialEmojis((prev) => [
          ...prev,
          {
            emotion: data.emotion,
            image_url: data.image_url,
            caption: data.caption,
            index: data.index,
          },
        ]);
      },
      onComplete: (data) => {
        const completeData = data as GenerateResponse;
        // complete 이벤트의 emojis가 비어있으면 스트리밍으로 받은 부분 결과 사용
        setPartialEmojis((prev) => {
          const finalEmojis = completeData.emojis?.length ? completeData.emojis : prev;
          setResult({ ...completeData, emojis: finalEmojis });
          return prev;
        });
        setGenerating(false);
      },
      onError: (err) => {
        setError(err.message);
        setGenerating(false);
      },
    });
  }, [session]);

  return { generating, partialEmojis, result, message, error, generate };
}
