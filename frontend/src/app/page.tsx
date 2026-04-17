"use client";

import { useRef, useState } from "react";
import PhotoUploader from "@/components/PhotoUploader";
import StyleSelector from "@/components/StyleSelector";
import EmojiGrid from "@/components/EmojiGrid";
import LoadingSpinner from "@/components/LoadingSpinner";
import FormatSelector from "@/components/FormatSelector";
import ProviderSelector from "@/components/ProviderSelector";
import CustomPrompt from "@/components/CustomPrompt";
import TierSelector from "@/components/TierSelector";
import SceneSelector from "@/components/SceneSelector";
import WizardContainer from "@/components/wizard/WizardContainer";
import type {
  GenerateResponse,
  EmojiStyle,
  ImageProvider,
  EmojiResult,
  Tier,
  WizardSession,
  Accessory,
  Background,
  TimeOfDay,
} from "@/types/api";
import { generateEmojisStream, type ProgressEvent } from "@/lib/sse";
import { wizardStart } from "@/lib/wizard-api";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [tier, setTier] = useState<Tier>("free");
  const [style, setStyle] = useState<EmojiStyle>("2d");
  const [provider, setProvider] = useState<ImageProvider>("openai");
  const [customPrompt, setCustomPrompt] = useState("");
  const [accessory, setAccessory] = useState<Accessory>("none");
  const [background, setBackground] = useState<Background>("white");
  const [timeOfDay, setTimeOfDay] = useState<TimeOfDay>("none");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // SSE 상태 (무료 플로우)
  const [progress, setProgress] = useState<ProgressEvent | null>(null);
  const [partialEmojis, setPartialEmojis] = useState<EmojiResult[]>([]);
  const abortRef = useRef<AbortController | null>(null);

  // 위자드 상태 (프리미엄/커스텀 플로우)
  const [wizardSession, setWizardSession] = useState<WizardSession | null>(null);

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
    setPreview(URL.createObjectURL(selectedFile));
    setResult(null);
    setError(null);
    setWizardSession(null);
  };

  // 무료 플로우: 바로 생성
  const handleFreeGenerate = () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setProgress(null);
    setPartialEmojis([]);

    abortRef.current = generateEmojisStream(
      file, style, 4, provider, customPrompt,
      {
        onProgress: (event) => setProgress(event),
        onEmoji: (event) => {
          setPartialEmojis((prev) => [
            ...prev,
            { emotion: event.emotion, image_url: event.image_url },
          ]);
        },
        onComplete: (data) => {
          setResult(data as GenerateResponse);
          setLoading(false);
          setProgress(null);
        },
        onError: (err) => {
          setError(err.message);
          setLoading(false);
          setProgress(null);
        },
      },
      accessory, background, timeOfDay,
    );
  };

  // 프리미엄/커스텀 플로우: 위자드 시작
  const handleWizardStart = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const session = await wizardStart(file, tier, provider, accessory, background, timeOfDay);
      setWizardSession(session);
    } catch (err) {
      setError(err instanceof Error ? err.message : "위자드 시작 실패");
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    abortRef.current?.abort();
    setLoading(false);
    setProgress(null);
    setPartialEmojis([]);
  };

  const isPremium = tier !== "free";

  return (
    <main className="max-w-4xl mx-auto px-4 py-12">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold text-orange-600 mb-3">🐾 PetMoji</h1>
        <p className="text-lg text-gray-600">
          반려동물 사진 한 장으로 나만의 캐릭터 이모지 세트를 만들어보세요
        </p>
      </div>

      {/* 위자드 모드 */}
      {wizardSession ? (
        <WizardContainer session={wizardSession} provider={provider} />
      ) : (
        <>
          {/* Upload Section */}
          <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
            <PhotoUploader onFileSelect={handleFileSelect} preview={preview} />

            {file && (
              <div className="mt-6 space-y-6">
                <TierSelector value={tier} onChange={setTier} />
                <ProviderSelector provider={provider} onProviderChange={setProvider} />

                {/* 무료: 스타일 + 커스텀 프롬프트 */}
                {!isPremium && (
                  <>
                    <StyleSelector style={style} onStyleChange={setStyle} />
                    <CustomPrompt value={customPrompt} onChange={setCustomPrompt} />
                  </>
                )}

                {/* 프리미엄: 장면 설정 (악세사리, 배경, 시간대) */}
                <SceneSelector
                  accessory={accessory}
                  background={background}
                  timeOfDay={timeOfDay}
                  onAccessoryChange={setAccessory}
                  onBackgroundChange={setBackground}
                  onTimeOfDayChange={setTimeOfDay}
                  isPremium={isPremium}
                />

                {loading ? (
                  <button
                    onClick={handleCancel}
                    className="w-full py-4 bg-red-400 hover:bg-red-500 text-white text-lg font-semibold rounded-xl transition-colors cursor-pointer"
                  >
                    ✕ 취소
                  </button>
                ) : isPremium ? (
                  <button
                    onClick={handleWizardStart}
                    className="w-full py-4 bg-orange-500 hover:bg-orange-600 text-white text-lg font-semibold rounded-xl transition-colors cursor-pointer"
                  >
                    🎨 가이드 위자드 시작
                  </button>
                ) : (
                  <button
                    onClick={handleFreeGenerate}
                    className="w-full py-4 bg-orange-500 hover:bg-orange-600 text-white text-lg font-semibold rounded-xl transition-colors cursor-pointer"
                  >
                    ✨ 이모지 세트 만들기
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Loading (무료 플로우) */}
          {loading && !isPremium && (
            <LoadingSpinner
              step={progress?.step}
              message={progress?.message}
              progress={progress?.progress}
              currentEmoji={progress?.current}
              totalEmojis={progress?.total}
              partialEmojis={partialEmojis}
            />
          )}

          {/* Loading (위자드 시작 중) */}
          {loading && isPremium && (
            <div className="bg-white rounded-2xl shadow-lg p-12 mb-8 text-center">
              <div className="animate-spin text-4xl mb-3">🔍</div>
              <p className="text-gray-500">반려동물을 분석하고 있어요...</p>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-8 text-red-700 text-center">
              {error}
            </div>
          )}

          {/* Results (무료 플로우) */}
          {result && (
            <div className="bg-white rounded-2xl shadow-lg p-8">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">
                  {result.pet_features.breed} 캐릭터 이모지
                </h2>
                <p className="text-gray-500 mt-1">
                  {result.pet_features.fur_color} · {result.pet_features.overall_vibe}
                </p>
              </div>
              <EmojiGrid emojis={result.emojis} />
              <FormatSelector emojis={result.emojis} />
            </div>
          )}
        </>
      )}
    </main>
  );
}
