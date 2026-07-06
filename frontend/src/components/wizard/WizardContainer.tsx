"use client";

import { useState, useCallback } from "react";
import type {
  WizardStep,
  EmojiStyle,
  Proportion,
  Reference,
  DetailOptions,
  WizardSession,
  ImageProvider,
  Accessory,
  Background,
  TimeOfDay,
  Tier,
} from "@/types/api";
import { wizardBack } from "@/lib/wizard-api";
import { useWizardPreview } from "./useWizardPreview";
import { useWizardGenerate } from "./useWizardGenerate";
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
  tier?: Tier;
}

const STEP_ORDER: WizardStep[] = ["style", "proportion", "detail", "reference", "scene", "generate"];

export default function WizardContainer({ session, provider: _provider, tier = "premium" }: Props) {
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
  const [backError, setBackError] = useState<string | null>(null);

  const getSelection = useCallback(() => {
    if (currentStep === "style") return { style };
    if (currentStep === "proportion") return { proportion };
    if (currentStep === "detail") return { detail };
    if (currentStep === "scene") return { scene };
    return { reference };
  }, [currentStep, style, proportion, detail, reference, scene]);

  const preview = useWizardPreview(session, currentStep, getSelection);
  const generation = useWizardGenerate(session);

  const allowedStyles = session.tier_config.styles || ["2d", "3d"];
  const maxEmotions = session.tier_config.max_emotions || 8;
  const currentIdx = STEP_ORDER.indexOf(currentStep);
  const error = backError ?? generation.error ?? preview.error;
  const message = generation.generating ? generation.message : preview.message;

  const handleConfirmStep = () => {
    const advance = () => {
      if (currentIdx < STEP_ORDER.length - 1) setCurrentStep(STEP_ORDER[currentIdx + 1]);
    };
    // 이미 미리보기가 있으면 바로 다음 단계로
    if (preview.previews[currentStep]) {
      advance();
      return;
    }
    preview.requestPreview(currentStep, getSelection(), { cacheBust: true, onSuccess: advance });
  };

  const handleBack = async () => {
    if (currentIdx <= 0) return;

    const targetStep = STEP_ORDER[currentIdx - 1];
    try {
      const result = await wizardBack(session.session_id, session.session_token, targetStep);
      setCurrentStep(targetStep);
      preview.setPreviews(result.previews);
      setBackError(null);
    } catch {
      setBackError("뒤로 가기 실패");
    }
  };

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
      {generation.result ? (
        <div>
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-gray-800">
              {session.pet_features.breed} 캐릭터 이모지
            </h2>
          </div>
          <EmojiGrid emojis={generation.result.emojis} />
          <FormatSelector emojis={generation.result.emojis} tier={tier} />
        </div>
      ) : generation.generating ? (
        <LoadingSpinner
          step="generating"
          message={message}
          progress={generation.partialEmojis.length / maxEmotions}
          currentEmoji={generation.partialEmojis.length}
          totalEmojis={maxEmotions}
          partialEmojis={generation.partialEmojis}
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
                  onClick={generation.generate}
                  className="flex-1 py-3 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-xl transition-colors cursor-pointer"
                >
                  ✨ 이모지 세트 만들기
                </button>
              ) : (
                <button
                  onClick={handleConfirmStep}
                  disabled={preview.loading}
                  className="flex-1 py-3 bg-orange-500 hover:bg-orange-600 disabled:bg-gray-300 text-white font-semibold rounded-xl transition-colors cursor-pointer disabled:cursor-not-allowed"
                >
                  {preview.loading ? "미리보기 생성 중..." : "다음 →"}
                </button>
              )}
            </div>
          </div>

          {/* 오른쪽: 미리보기 */}
          <PreviewPanel
            imageUrl={
              preview.previews[currentStep] || preview.previews[STEP_ORDER[currentIdx - 1]] || null
            }
            loading={preview.loading}
            message={preview.message}
          />
        </div>
      )}
    </div>
  );
}
