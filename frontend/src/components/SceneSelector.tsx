"use client";

import type { Accessory, Background, TimeOfDay } from "@/types/api";

const ACCESSORIES: { id: Accessory; icon: string; label: string }[] = [
  { id: "none", icon: "🚫", label: "없음" },
  { id: "ribbon", icon: "🎀", label: "리본" },
  { id: "bowtie", icon: "🤵", label: "나비넥타이" },
  { id: "crown", icon: "👑", label: "왕관" },
  { id: "flower", icon: "🌸", label: "꽃" },
  { id: "glasses", icon: "👓", label: "안경" },
  { id: "hat", icon: "🧢", label: "모자" },
  { id: "scarf", icon: "🧣", label: "목도리" },
  { id: "bandana", icon: "🏴", label: "반다나" },
  { id: "headband", icon: "🐰", label: "머리띠" },
];

const BACKGROUNDS: { id: Background; icon: string; label: string }[] = [
  { id: "white", icon: "⬜", label: "흰색" },
  { id: "transparent", icon: "🔲", label: "투명" },
  { id: "gradient", icon: "🌈", label: "그라데이션" },
  { id: "park", icon: "🌳", label: "공원" },
  { id: "room", icon: "🛋️", label: "방" },
  { id: "cafe", icon: "☕", label: "카페" },
  { id: "beach", icon: "🏖️", label: "해변" },
  { id: "snow", icon: "❄️", label: "눈" },
  { id: "sky", icon: "☁️", label: "하늘" },
  { id: "night", icon: "🌙", label: "밤" },
];

const TIMES: { id: TimeOfDay; icon: string; label: string }[] = [
  { id: "none", icon: "🚫", label: "기본" },
  { id: "morning", icon: "🌅", label: "아침" },
  { id: "afternoon", icon: "☀️", label: "낮" },
  { id: "sunset", icon: "🌇", label: "노을" },
  { id: "night", icon: "🌙", label: "밤" },
];

interface Props {
  accessory: Accessory;
  background: Background;
  timeOfDay: TimeOfDay;
  onAccessoryChange: (v: Accessory) => void;
  onBackgroundChange: (v: Background) => void;
  onTimeOfDayChange: (v: TimeOfDay) => void;
  isPremium: boolean;
}

function OptionGrid<T extends string>({
  title,
  options,
  value,
  onChange,
  disabled,
}: {
  title: string;
  options: { id: T; icon: string; label: string }[];
  value: T;
  onChange: (v: T) => void;
  disabled: boolean;
}) {
  return (
    <div className="mb-4">
      <h4 className="text-sm font-semibold text-gray-700 mb-2">{title}</h4>
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => (
          <button
            key={opt.id}
            onClick={() => onChange(opt.id)}
            disabled={disabled}
            className={`px-3 py-1.5 rounded-lg text-sm border transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed ${
              value === opt.id
                ? "border-orange-400 bg-orange-50 text-orange-700"
                : "border-gray-200 hover:border-orange-300 text-gray-600"
            }`}
          >
            <span className="mr-1">{opt.icon}</span>
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function SceneSelector({
  accessory,
  background,
  timeOfDay,
  onAccessoryChange,
  onBackgroundChange,
  onTimeOfDayChange,
  isPremium,
}: Props) {
  if (!isPremium) {
    return (
      <div className="bg-gray-50 rounded-xl p-4 text-center text-sm text-gray-500">
        배경, 악세사리, 시간대 설정은 프리미엄 이상에서 사용 가능합니다
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <h3 className="text-base font-bold text-gray-800 mb-3">
        장면 설정
      </h3>
      <OptionGrid
        title="악세사리"
        options={ACCESSORIES}
        value={accessory}
        onChange={onAccessoryChange}
        disabled={false}
      />
      <OptionGrid
        title="배경"
        options={BACKGROUNDS}
        value={background}
        onChange={onBackgroundChange}
        disabled={false}
      />
      <OptionGrid
        title="시간대"
        options={TIMES}
        value={timeOfDay}
        onChange={onTimeOfDayChange}
        disabled={false}
      />
    </div>
  );
}
