"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { WizardSession, WizardStep } from "@/types/api";
import { wizardStep } from "@/lib/wizard-api";

const DEBOUNCE_MS = 1500;

interface PreviewOptions {
  /** 확정 요청 시 브라우저 캐시 우회용 타임스탬프 부착 */
  cacheBust?: boolean;
  /** 미리보기 수신 후 실행 (예: 다음 단계로 이동) */
  onSuccess?: () => void;
}

/** 단계별 미리보기 상태 관리 — 요청, 디바운스 자동 갱신, 로딩/에러 */
export function useWizardPreview(
  session: WizardSession,
  currentStep: WizardStep,
  getSelection: () => Record<string, unknown>
) {
  const [previews, setPreviews] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSelectionRef = useRef<string>("");

  const requestPreview = useCallback(
    (step: WizardStep, selection: Record<string, unknown>, options: PreviewOptions = {}) => {
      if (abortRef.current) abortRef.current.abort();
      setLoading(true);
      setError(null);

      abortRef.current = wizardStep(session.session_id, session.session_token, step, selection, {
        onProgress: (data) => setMessage(data.message),
        onPreview: (data) => {
          let url = data.image_url;
          if (options.cacheBust) {
            url += (url.includes("?") ? "&" : "?") + `_t=${Date.now()}`;
          }
          setPreviews((prev) => ({ ...prev, [step]: url }));
          setLoading(false);
          options.onSuccess?.();
        },
        onError: (err) => {
          setError(err.message);
          setLoading(false);
        },
      });
    },
    [session.session_id, session.session_token]
  );

  // 옵션 변경 시 디바운스로 자동 미리보기
  useEffect(() => {
    if (currentStep === "generate") return;

    const selectionKey = JSON.stringify({ currentStep, ...getSelection() });
    if (selectionKey === lastSelectionRef.current) return;

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      lastSelectionRef.current = selectionKey;
      requestPreview(currentStep, getSelection());
    }, DEBOUNCE_MS);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [currentStep, getSelection, requestPreview]);

  return { previews, setPreviews, loading, message, error, requestPreview };
}
