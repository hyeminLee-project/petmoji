import type { Reference } from "@/types/api";

const REFERENCES: { id: Reference; icon: string; name: string; desc: string }[] = [
  { id: "kakao", icon: "🟡", name: "카카오프렌즈", desc: "라이언, 어피치 스타일" },
  { id: "line", icon: "🟤", name: "라인프렌즈", desc: "브라운, 코니 스타일" },
  { id: "sanrio", icon: "🎀", name: "산리오", desc: "헬로키티, 마이멜로디 스타일" },
  { id: "popmart", icon: "🎁", name: "팝마트", desc: "디자이너 토이 스타일" },
  { id: "none", icon: "✨", name: "없음", desc: "레퍼런스 없이 자유롭게" },
];

interface Props {
  value: Reference;
  onChange: (reference: Reference) => void;
}

export default function ReferenceStep({ value, onChange }: Props) {
  return (
    <div>
      <h3 className="text-lg font-bold text-gray-800 mb-4">Step 4. 레퍼런스 스타일</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {REFERENCES.map((ref) => (
          <button
            key={ref.id}
            onClick={() => onChange(ref.id)}
            className={`p-4 rounded-xl border-2 text-center transition-colors cursor-pointer ${
              value === ref.id
                ? "border-orange-400 bg-orange-50"
                : "border-gray-200 hover:border-orange-300"
            }`}
          >
            <div className="text-2xl mb-1">{ref.icon}</div>
            <div className="font-medium text-sm">{ref.name}</div>
            <div className="text-xs text-gray-500">{ref.desc}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
