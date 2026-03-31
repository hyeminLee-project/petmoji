import type { Tier } from "@/types/api";

const TIERS: { id: Tier; icon: string; name: string; desc: string; badge?: string }[] = [
  { id: "free", icon: "🆓", name: "무료", desc: "2D/3D, 4개 이모지" },
  { id: "premium", icon: "💎", name: "프리미엄", desc: "5 스타일, 16개, 가이드 위자드", badge: "추천" },
  { id: "custom", icon: "🎨", name: "커스텀", desc: "자유 프롬프트, 무제한" },
];

interface Props {
  value: Tier;
  onChange: (tier: Tier) => void;
}

export default function TierSelector({ value, onChange }: Props) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">플랜</label>
      <div className="grid grid-cols-3 gap-3">
        {TIERS.map((tier) => (
          <button
            key={tier.id}
            onClick={() => onChange(tier.id)}
            className={`relative p-3 rounded-xl border-2 text-center transition-colors cursor-pointer ${
              value === tier.id
                ? "border-orange-400 bg-orange-50"
                : "border-gray-200 hover:border-orange-300"
            }`}
          >
            {tier.badge && (
              <span className="absolute -top-2 right-2 bg-orange-500 text-white text-xs px-2 py-0.5 rounded-full">
                {tier.badge}
              </span>
            )}
            <div className="text-xl mb-1">{tier.icon}</div>
            <div className="font-medium text-sm">{tier.name}</div>
            <div className="text-xs text-gray-500">{tier.desc}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
