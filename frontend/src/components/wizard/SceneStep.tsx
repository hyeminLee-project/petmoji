import type { Accessory, Background, TimeOfDay } from "@/types/api";

export interface SceneOptions {
  accessory: Accessory;
  scene_background: Background;
  time_of_day: TimeOfDay;
}

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
  { id: "white", icon: "⬜", label: "없음" },
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
  value: SceneOptions;
  onChange: (scene: SceneOptions) => void;
}

function OptionGrid<T extends string>({
  title,
  options,
  value,
  onChange,
}: {
  title: string;
  options: { id: T; icon: string; label: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-600 mb-2">{title}</label>
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => (
          <button
            key={opt.id}
            onClick={() => onChange(opt.id)}
            className={`px-3 py-1.5 rounded-lg text-sm border transition-all cursor-pointer ${
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

export default function SceneStep({ value, onChange }: Props) {
  return (
    <div>
      <h3 className="text-lg font-bold text-gray-800 mb-4">Step 5. 장면 설정</h3>
      <div className="space-y-2">
        <OptionGrid
          title="악세사리"
          options={ACCESSORIES}
          value={value.accessory}
          onChange={(v) => onChange({ ...value, accessory: v })}
        />
        <OptionGrid
          title="장면 배경"
          options={BACKGROUNDS}
          value={value.scene_background}
          onChange={(v) => onChange({ ...value, scene_background: v })}
        />
        <OptionGrid
          title="시간대"
          options={TIMES}
          value={value.time_of_day}
          onChange={(v) => onChange({ ...value, time_of_day: v })}
        />
      </div>
    </div>
  );
}
