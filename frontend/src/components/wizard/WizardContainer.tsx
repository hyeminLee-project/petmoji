"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import type {
  WizardStep,
  EmojiStyle,
  Proportion,
  Reference,
  DetailOptions,
  WizardSession,
  ImageProvider,
  EmojiResult,
  GenerateResponse,
  Accessory,
  Background,
  TimeOfDay,
} from "@/types/api";
import { wizardStep, wizardBack, wizardGenerate } from "@/lib/wizard-api";
import StepIndicator from "./StepIndicator";
import StyleStep from "./StyleStep";
import ProportionStep from "./ProportionStep";
import DetailStep from "./DetailStep";
import ReferenceStep from "./ReferenceStep";
import SceneStep from "./SceneStep";
import type { SceneOptions } from "./SceneStep";
import PreviewPanel from "./PreviewPanel";
import EmojiGrid from "@/components/EmojiGrid";
import FormatSelector from "@/components/FormatSelector";
import LoadingSpinner from "@/components/LoadingSpinner";

interface Props {
  session: WizardSession;
  provider: ImageProvider;
}

const STEP_ORDER: WizardStep[] = ["style", "proportion", "detail", "reference", "scene", "generate"];

export default function WizardContainer({ session, provider: _provider }: Props) {
  const [currentStep, setCurrentStep] = useState<WizardStep>("style");
  const [style, setStyle] = useState<EmojiStyle>("2d");
  const [proportion, setProportion] = useState<Proportion>("chibi");
  const [detail, setDetail] = useState<DetailOptions>({
    eye_size: "big",
    outline: "bold",
    background: "white",
  });
  const [reference, setReference] = useState<Reference>("none");
  const [scene, setScene] = useState<SceneOptions>({
    accessory: "none" as Accessory,
    scene_background: "white" as Background,
    time_of_day: "none" as TimeOfDay,
  });

  const [previews, setPreviews] = useState<Record<string, string>>({});
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewMessage, setPreviewMessage] = useState("");

  const [generating, setGenerating] = useState(false);
  const [partialEmojis, setPartialEmojis] = useState<EmojiResult[]>([]);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const allowedStyles = (session.tier_config as { styles?: string[] }).styles || ["2d", "3d"];
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const getSelection = useCallback(() => {
    if (currentStep === "style") return { style };
    if (currentStep === "proportion") return { proportion };
    if (currentStep === "detail") return { detail };
    if (currentStep === "scene") return { scene };
    return { reference };
  }, [currentStep, style, proportion, detail, reference, scene]);

  const abortRef = useRef<AbortController | null>(null);

  const requestPreview = useCallback((step: WizardStep, selection: Record<string, unknown>) => {
    if (abortRef.current) abortRef.current.abort();
    setPreviewLoading(true);
    setError(null);

    abortRef.current = wizardStep(session.session_id, session.session_token, step, selection, {
      onProgress: (data) => setPreviewMessage(data.message),
      onPreview: (data) => {
        setPreviews((prev) => ({ ...prev, [step]: data.image_url }));
        setPreviewLoading(false);
      },
      onError: (err) => {
        setError(err.message);
        setPreviewLoading(false);
      },
    });
  }, [session.session_id, session.session_token]);

  // 옵션 변경 시 1.5초 디바운스로 자동 미리보기
  const lastSelectionRef = useRef<string>("");
  useEffect(() => {
    if (currentStep === "generate") return;

    const selectionKey = JSON.stringify({ currentStep, ...getSelection() });
    if (selectionKey === lastSelectionRef.current) return;

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      lastSelectionRef.current = selectionKey;
      requestPreview(currentStep, getSelection());
    }, 1500);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [style, proportion, detail, reference, scene, currentStep, getSelection, requestPreview]);

  const handleConfirmStep = () => {
    // 이미 미리보기가 있으면 바로 다음 단계로
    const idx = STEP_ORDER.indexOf(currentStep);
    if (previews[currentStep] && idx < STEP_ORDER.length - 1) {
      setCurrentStep(STEP_ORDER[idx + 1]);
      return;
    }

    // 미리보기 없으면 요청 후 다음 단계로
    setPreviewLoading(true);
    setError(null);

    wizardStep(session.session_id, session.session_token, currentStep, getSelection(), {
      onProgress: (data) => setPreviewMessage(data.message),
      onPreview: (data) => {
        const url = data.image_url.includes("?")
          ? `${data.image_url}&_t=${Date.now()}`
          : `${data.image_url}?_t=${Date.now()}`;
        setPreviews((prev) => ({ ...prev, [currentStep]: url }));
        setPreviewLoading(false);
        if (idx < STEP_ORDER.length - 1) {
          setCurrentStep(STEP_ORDER[idx + 1]);
        }
      },
      onError: (err) => {
        setError(err.message);
        setPreviewLoading(false);
      },
    });
  };

  const handleBack = async () => {
    const idx = STEP_ORDER.indexOf(currentStep);
    if (idx <= 0) return;

    const targetStep = STEP_ORDER[idx - 1];
    try {
      const result = await wizardBack(session.session_id, session.session_token, targetStep);
      setCurrentStep(targetStep as WizardStep);
      setPreviews(result.previews);
    } catch {
      setError("뒤로 가기 실패");
    }
  };

  const handleGenerate = () => {
    setGenerating(true);
    setPartialEmojis([]);
    setError(null);

    const maxEmotions = (session.tier_config as { max_emotions?: number }).max_emotions || 8;

    wizardGenerate(session.session_id, session.session_token, maxEmotions, {
      onProgress: (data) => setPreviewMessage(data.message),
      onEmoji: (data) => {
        setPartialEmojis((prev) => [
          ...prev,
          { emotion: data.emotion, image_url: data.image_url },
        ]);
      },
      onComplete: (data) => {
        const completeData = data as GenerateResponse;
        // complete 이벤트의 emojis가 비어있으면 partialEmojis로 대체
        setPartialEmojis((prev) => {
          const finalEmojis = completeData.emojis?.length ? completeData.emojis : prev;
          setResult({
            ...completeData,
            emojis: finalEmojis,
          });
          return prev;
        });
        setGenerating(false);
      },
      onError: (err) => {
        setError(err.message);
        setGenerating(false);
      },
    });
  };

  const currentIdx = STEP_ORDER.indexOf(currentStep);

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8">
      <StepIndicator
        currentStep={currentStep}
        onStepClick={(step) => {
          const idx = STEP_ORDER.indexOf(step);
          if (idx < currentIdx) setCurrentStep(step);
        }}
      />

      {/* 결과 화면 */}
      {result ? (
        <div>
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-gray-800">
              {session.pet_features.breed} 캐릭터 이모지
            </h2>
          </div>
          <EmojiGrid emojis={result.emojis} />
          <FormatSelector emojis={result.emojis} />
        </div>
      ) : generating ? (
        <LoadingSpinner
          step="generating"
          message={previewMessage}
          progress={partialEmojis.length / ((session.tier_config as { max_emotions?: number }).max_emotions || 8)}
          currentEmoji={partialEmojis.length}
          totalEmojis={(session.tier_config as { max_emotions?: number }).max_emotions || 8}
          partialEmojis={partialEmojis}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 왼쪽: 옵션 선택 */}
          <div>
            {currentStep === "style" && (
              <StyleStep value={style} onChange={setStyle} allowedStyles={allowedStyles} />
            )}
            {currentStep === "proportion" && (
              <ProportionStep value={proportion} onChange={setProportion} />
            )}
            {currentStep === "detail" && (
              <DetailStep value={detail} onChange={setDetail} />
            )}
            {currentStep === "reference" && (
              <ReferenceStep value={reference} onChange={setReference} />
            )}
            {currentStep === "scene" && (
              <SceneStep value={scene} onChange={setScene} />
            )}
            {currentStep === "generate" && (
              <div className="text-center py-8">
                <div className="text-4xl mb-3">✨</div>
                <h3 className="text-lg font-bold text-gray-800 mb-2">준비 완료!</h3>
                <p className="text-gray-500 text-sm">설정을 확인하고 이모지 세트를 생성하세요</p>
              </div>
            )}

            {/* 에러 */}
            {error && (
              <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">
                {error}
              </div>
            )}

            {/* 버튼 */}
            <div className="flex gap-3 mt-6">
              {currentIdx > 0 && (
                <button
                  onClick={handleBack}
                  className="flex-1 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-xl transition-colors cursor-pointer"
                >
                  ← 이전
                </button>
              )}
              {currentStep === "generate" ? (
                <button
                  onClick={handleGenerate}
                  className="flex-1 py-3 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-xl transition-colors cursor-pointer"
                >
                  ✨ 이모지 세트 만들기
                </button>
              ) : (
                <button
                  onClick={handleConfirmStep}
                  disabled={previewLoading}
                  className="flex-1 py-3 bg-orange-500 hover:bg-orange-600 disabled:bg-gray-300 text-white font-semibold rounded-xl transition-colors cursor-pointer disabled:cursor-not-allowed"
                >
                  {previewLoading ? "미리보기 생성 중..." : "다음 →"}
                </button>
              )}
            </div>
          </div>

          {/* 오른쪽: 미리보기 */}
          <PreviewPanel
            imageUrl={previews[currentStep] || previews[STEP_ORDER[currentIdx - 1]] || null}
            loading={previewLoading}
            message={previewMessage}
          />
        </div>
      )}
    </div>
  );
}
