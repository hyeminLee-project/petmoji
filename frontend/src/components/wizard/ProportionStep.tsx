import type { Proportion } from "@/types/api";

const PROPORTIONS: { id: Proportion; icon: string; name: string; desc: string }[] = [
  { id: "chibi", icon: "🍡", name: "치비", desc: "큰 머리, 작은 몸 (2:1)" },
  { id: "normal", icon: "🧑", name: "일반", desc: "약간 큰 머리 (3:1)" },
  { id: "realistic", icon: "🐕", name: "리얼", desc: "자연스러운 비율" },
];

interface Props {
  value: Proportion;
  onChange: (proportion: Proportion) => void;
}

export default function ProportionStep({ value, onChange }: Props) {
  return (
    <div>
      <h3 className="text-lg font-bold text-gray-800 mb-4">Step 2. 캐릭터 비율</h3>
      <div className="grid grid-cols-3 gap-3">
        {PROPORTIONS.map((p) => (
          <button
            key={p.id}
            onClick={() => onChange(p.id)}
            className={`p-4 rounded-xl border-2 text-center transition-colors cursor-pointer ${
              value === p.id
                ? "border-orange-400 bg-orange-50"
                : "border-gray-200 hover:border-orange-300"
            }`}
          >
            <div className="text-2xl mb-1">{p.icon}</div>
            <div className="font-medium text-sm">{p.name}</div>
            <div className="text-xs text-gray-500">{p.desc}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
