"use client";

import { useRef, useState } from "react";
import PhotoUploader from "@/components/PhotoUploader";
import StyleSelector from "@/components/StyleSelector";
import EmojiGrid from "@/components/EmojiGrid";
import LoadingSpinner from "@/components/LoadingSpinner";
import FormatSelector from "@/components/FormatSelector";
import ProviderSelector from "@/components/ProviderSelector";
import CustomPrompt from "@/components/CustomPrompt";
import type { GenerateResponse, EmojiStyle, ImageProvider, EmojiResult } from "@/types/api";
import { generateEmojisStream, type ProgressEvent } from "@/lib/sse";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [style, setStyle] = useState<EmojiStyle>("2d");
  const [provider, setProvider] = useState<ImageProvider>("openai");
  const [customPrompt, setCustomPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // SSE 상태
  const [progress, setProgress] = useState<ProgressEvent | null>(null);
  const [partialEmojis, setPartialEmojis] = useState<EmojiResult[]>([]);
  const abortRef = useRef<AbortController | null>(null);

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
    setPreview(URL.createObjectURL(selectedFile));
    setResult(null);
    setError(null);
  };

  const handleGenerate = () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setProgress(null);
    setPartialEmojis([]);

    abortRef.current = generateEmojisStream(
      file,
      style,
      8,
      provider,
      customPrompt,
      {
        onProgress: (event) => {
          setProgress(event);
        },
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
      }
    );
  };

  const handleCancel = () => {
    abortRef.current?.abort();
    setLoading(false);
    setProgress(null);
    setPartialEmojis([]);
  };

  return (
    <main className="max-w-4xl mx-auto px-4 py-12">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold text-orange-600 mb-3">
          🐾 PetMoji
        </h1>
        <p className="text-lg text-gray-600">
          반려동물 사진 한 장으로 나만의 캐릭터 이모지 세트를 만들어보세요
        </p>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
        <PhotoUploader
          onFileSelect={handleFileSelect}
          preview={preview}
        />

        {file && (
          <div className="mt-6 space-y-6">
            <StyleSelector style={style} onStyleChange={setStyle} />
            <ProviderSelector provider={provider} onProviderChange={setProvider} />
            <CustomPrompt value={customPrompt} onChange={setCustomPrompt} />

            {loading ? (
              <button
                onClick={handleCancel}
                className="w-full py-4 bg-red-400 hover:bg-red-500 text-white text-lg font-semibold rounded-xl transition-colors cursor-pointer"
              >
                ✕ 생성 취소
              </button>
            ) : (
              <button
                onClick={handleGenerate}
                className="w-full py-4 bg-orange-500 hover:bg-orange-600 text-white text-lg font-semibold rounded-xl transition-colors cursor-pointer"
              >
                ✨ 이모지 세트 만들기
              </button>
            )}
          </div>
        )}
      </div>

      {/* Loading with progress */}
      {loading && (
        <LoadingSpinner
          step={progress?.step}
          message={progress?.message}
          progress={progress?.progress}
          currentEmoji={progress?.current}
          totalEmojis={progress?.total}
          partialEmojis={partialEmojis}
        />
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-8 text-red-700 text-center">
          {error}
        </div>
      )}

      {/* Results */}
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
    </main>
  );
}
