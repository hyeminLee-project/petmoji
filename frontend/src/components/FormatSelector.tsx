"use client";

import { useEffect, useState } from "react";
import type { ConvertFormat, EmojiResult, ConvertedEmoji, FormatInfo, Tier } from "@/types/api";
import { convertEmojis, animateEmoji, getFormats } from "@/lib/api";

interface Props {
  emojis: EmojiResult[];
  tier?: Tier;
}

export default function FormatSelector({ emojis, tier = "free" }: Props) {
  const [formats, setFormats] = useState<FormatInfo[]>([]);
  const [converting, setConverting] = useState<ConvertFormat | null>(null);
  const [results, setResults] = useState<Record<string, ConvertedEmoji[]>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getFormats()
      .then(setFormats)
      .catch(() => setError("포맷 목록을 불러오지 못했습니다"));
  }, []);

  const [animating, setAnimating] = useState<string | null>(null);
  const [animated, setAnimated] = useState<Record<string, ConvertedEmoji>>({});
  const [animateError, setAnimateError] = useState<string | null>(null);

  const handleAnimate = async (emoji: EmojiResult) => {
    if (animating || animated[emoji.emotion]) return;

    setAnimating(emoji.emotion);
    setAnimateError(null);

    try {
      const result = await animateEmoji(emoji, tier);
      setAnimated((prev) => ({ ...prev, [emoji.emotion]: result }));
    } catch (err) {
      setAnimateError(err instanceof Error ? err.message : "생성 실패");
    } finally {
      setAnimating(null);
    }
  };

  const handleConvert = async (format: ConvertFormat) => {
    if (results[format]) return; // 이미 변환됨

    setConverting(format);
    setError(null);

    try {
      const data = await convertEmojis(emojis, format);
      setResults((prev) => ({ ...prev, [format]: data.emojis }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "변환 실패");
    } finally {
      setConverting(null);
    }
  };

  const handleDownload = (emoji: ConvertedEmoji) => {
    const link = document.createElement("a");
    link.href = emoji.image_url;
    if (emoji.format === "kakao_submission") {
      link.download = "petmoji-kakao-submission.zip";
    } else {
      const ext = emoji.format === "gif" || emoji.format === "animated" ? "gif" : "png";
      link.download = `petmoji-${emoji.format}-${emoji.emotion}.${ext}`;
    }
    link.click();
  };

  const handleDownloadAll = (format: string) => {
    const items = results[format];
    if (!items) return;
    items.forEach((emoji, i) => {
      setTimeout(() => handleDownload(emoji), i * 200);
    });
  };

  return (
    <div className="mt-8">
      <h3 className="text-lg font-bold text-gray-800 mb-4">
        📦 플랫폼별 변환
      </h3>

      {/* Format buttons */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        {formats.map((fmt) => (
          <button
            key={fmt.id}
            onClick={() => handleConvert(fmt.id)}
            disabled={converting !== null}
            className={`p-3 rounded-xl border-2 text-center transition-all cursor-pointer disabled:cursor-not-allowed ${
              results[fmt.id]
                ? "border-green-400 bg-green-50"
                : converting === fmt.id
                  ? "border-orange-400 bg-orange-50 animate-pulse"
                  : "border-gray-200 hover:border-orange-300"
            }`}
          >
            <div className="text-xl">{fmt.icon}</div>
            <div className="text-sm font-medium mt-1">{fmt.name}</div>
            <div className="text-xs text-gray-500">{fmt.description}</div>
            {results[fmt.id] && (
              <div className="text-xs text-green-600 mt-1">✅ 완료</div>
            )}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-3 mb-4 text-red-700 text-sm text-center">
          {error}
        </div>
      )}

      {/* 움직이는 이모지 (AI 영상 생성) */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-semibold text-gray-700">🎬 움직이는 이모지 (AI)</h4>
          <span className="text-xs text-gray-400">개당 1~2분 소요</span>
        </div>

        {tier === "free" ? (
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-center text-sm text-gray-500">
            🔒 프리미엄 티어 전용 기능입니다
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {emojis.map((emoji) => {
              const done = animated[emoji.emotion];
              const isRunning = animating === emoji.emotion;
              return (
                <div
                  key={`animate-${emoji.emotion}`}
                  className="group relative bg-gray-50 rounded-lg p-2 text-center"
                >
                  <img
                    src={done ? done.image_url : emoji.image_url}
                    alt={emoji.emotion}
                    className="w-full aspect-square object-contain rounded-lg mb-1"
                  />
                  <p className="text-xs text-gray-600 mb-1">{emoji.emotion}</p>
                  {done ? (
                    <button
                      onClick={() => handleDownload(done)}
                      className="w-full py-1 text-xs bg-green-100 text-green-700 rounded-lg cursor-pointer"
                    >
                      ✅ 완료 · 다운로드
                    </button>
                  ) : isRunning ? (
                    <div className="w-full py-1 text-xs bg-orange-100 text-orange-600 rounded-lg animate-pulse">
                      생성 중... (1~2분)
                    </div>
                  ) : (
                    <button
                      onClick={() => handleAnimate(emoji)}
                      disabled={animating !== null}
                      className="w-full py-1 text-xs bg-orange-500 hover:bg-orange-600 text-white rounded-lg transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      ▶ 움직이기
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {animateError && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-3 mt-3 text-red-700 text-sm text-center">
            {animateError}
          </div>
        )}
      </div>

      {/* Converted results */}
      {Object.entries(results).map(([format, convertedEmojis]) => (
        <div key={format} className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-semibold text-gray-700">
              {formats.find((f) => f.id === format)?.name} 결과
            </h4>
            <button
              onClick={() => handleDownloadAll(format)}
              className="text-sm text-orange-600 hover:text-orange-700 cursor-pointer"
            >
              📦 전체 다운로드
            </button>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {convertedEmojis.map((emoji) => (
              <div
                key={`${format}-${emoji.emotion}`}
                className="group relative bg-gray-50 rounded-lg p-2 text-center"
              >
                <img
                  src={emoji.image_url}
                  alt={emoji.emotion}
                  className="w-full aspect-square object-contain rounded-lg mb-1"
                />
                <p className="text-xs text-gray-600">{emoji.emotion}</p>
                <p className="text-xs text-gray-400">
                  {emoji.width}x{emoji.height}
                </p>
                <button
                  onClick={() => handleDownload(emoji)}
                  className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 bg-white/80 rounded-full p-1 text-xs transition-opacity cursor-pointer"
                >
                  ⬇️
                </button>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
