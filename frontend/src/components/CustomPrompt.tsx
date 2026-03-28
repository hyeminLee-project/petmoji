"use client";

import { useState } from "react";

const PRESETS = [
  { label: "리드줄 빼기", value: "Remove any leash or accessories" },
  { label: "눈 더 크게", value: "Make the eyes much bigger and more sparkly" },
  { label: "더 심플하게", value: "Minimal design, fewer details, thicker outlines, like Kakao Friends Ryan" },
  { label: "더 귀엽게", value: "Extra cute, bigger head ratio, blushing cheeks, tiny body" },
  { label: "수채화 스타일", value: "Watercolor painting style with soft edges and pastel colors" },
  { label: "픽셀아트", value: "Pixel art style, 32x32 retro game character look" },
];

interface Props {
  value: string;
  onChange: (value: string) => void;
}

export default function CustomPrompt({ value, onChange }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="text-sm text-orange-600 hover:text-orange-700 cursor-pointer"
      >
        {isOpen ? "▾ 스타일 커스터마이징 닫기" : "▸ 스타일 커스터마이징 (선택)"}
      </button>

      {isOpen && (
        <div className="mt-3 space-y-3">
          {/* Preset chips */}
          <div className="flex flex-wrap gap-2">
            {PRESETS.map((preset) => (
              <button
                key={preset.label}
                type="button"
                onClick={() => {
                  const newValue = value
                    ? `${value}. ${preset.value}`
                    : preset.value;
                  onChange(newValue);
                }}
                className="px-3 py-1.5 text-xs bg-orange-50 text-orange-700 rounded-full border border-orange-200 hover:bg-orange-100 transition-colors cursor-pointer"
              >
                {preset.label}
              </button>
            ))}
          </div>

          {/* Custom text input */}
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="예: 눈을 더 크게, 리드줄 빼고, 춘식이처럼 둥글둥글하게..."
            className="w-full p-3 border border-gray-200 rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-orange-300"
            rows={3}
          />

          {value && (
            <button
              type="button"
              onClick={() => onChange("")}
              className="text-xs text-gray-400 hover:text-gray-600 cursor-pointer"
            >
              ✕ 초기화
            </button>
          )}
        </div>
      )}
    </div>
  );
}
