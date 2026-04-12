"use client";

import { useState } from "react";
import type { ConvertFormat, EmojiResult, ConvertedEmoji } from "@/types/api";
import { convertEmojis } from "@/lib/api";

const FORMATS: { id: ConvertFormat; icon: string; name: string; desc: string }[] = [
  { id: "kakao", icon: "💬", name: "카카오톡", desc: "360x360 (최대 32개)" },
  { id: "kakao_animated", icon: "💬", name: "카카오 움직이는", desc: "360x360 GIF (최대 24개)" },
  { id: "kakao_large_square", icon: "💬", name: "카카오 큰(정사각)", desc: "540x540 (최대 16개)" },
  { id: "kakao_large_wide", icon: "💬", name: "카카오 큰(가로)", desc: "540x300 (최대 16개)" },
  { id: "kakao_large_tall", icon: "💬", name: "카카오 큰(세로)", desc: "300x540 (최대 16개)" },
  { id: "imessage", icon: "🍎", name: "iMessage", desc: "408x408 스티커" },
  { id: "sticker", icon: "✂️", name: "스티커 PNG", desc: "512x512 투명 배경" },
  { id: "gif", icon: "🎬", name: "움직이는 GIF", desc: "256x256 바운스" },
  { id: "wallpaper", icon: "📱", name: "폰 배경화면", desc: "1170x2532 패턴" },
];

interface Props {
  emojis: EmojiResult[];
}

export default function FormatSelector({ emojis }: Props) {
  const [converting, setConverting] = useState<ConvertFormat | null>(null);
  const [results, setResults] = useState<Record<string, ConvertedEmoji[]>>({});
  const [error, setError] = useState<string | null>(null);

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
    const ext = emoji.format === "gif" ? "gif" : "png";
    link.download = `petmoji-${emoji.format}-${emoji.emotion}.${ext}`;
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
        {FORMATS.map((fmt) => (
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
            <div className="text-xs text-gray-500">{fmt.desc}</div>
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

      {/* Converted results */}
      {Object.entries(results).map(([format, convertedEmojis]) => (
        <div key={format} className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-semibold text-gray-700">
              {FORMATS.find((f) => f.id === format)?.name} 결과
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
