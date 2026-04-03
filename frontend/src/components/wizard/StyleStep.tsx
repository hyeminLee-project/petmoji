import type { EmojiStyle } from "@/types/api";

const STYLES: { id: EmojiStyle; icon: string; name: string; desc: string }[] = [
  { id: "2d", icon: "✏️", name: "2D 캐릭터", desc: "카카오프렌즈 스타일" },
  { id: "3d", icon: "🧸", name: "3D 캐릭터", desc: "팝마트 피규어 스타일" },
  { id: "watercolor", icon: "🎨", name: "수채화", desc: "파스텔 수채화 스타일" },
  { id: "pixel", icon: "👾", name: "픽셀아트", desc: "레트로 게임 스타일" },
  { id: "realistic", icon: "📷", name: "사실풍", desc: "디지털 페인팅 스타일" },
];

interface Props {
  value: EmojiStyle;
  onChange: (style: EmojiStyle) => void;
  allowedStyles: string[];
}

export default function StyleStep({ value, onChange, allowedStyles }: Props) {
  return (
    <div>
      <h3 className="text-lg font-bold text-gray-800 mb-4">Step 1. 스타일 선택</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {STYLES.map((style) => {
          const isAllowed = allowedStyles.includes(style.id);
          return (
            <button
              key={style.id}
              onClick={() => isAllowed && onChange(style.id)}
              disabled={!isAllowed}
              className={`p-4 rounded-xl border-2 text-center transition-colors ${
                value === style.id
                  ? "border-orange-400 bg-orange-50"
                  : isAllowed
                    ? "border-gray-200 hover:border-orange-300 cursor-pointer"
                    : "border-gray-100 bg-gray-50 opacity-50 cursor-not-allowed"
              }`}
            >
              <div className="text-2xl mb-1">{style.icon}</div>
              <div className="font-medium text-sm">{style.name}</div>
              <div className="text-xs text-gray-500">{style.desc}</div>
              {!isAllowed && <div className="text-xs text-orange-500 mt-1">PRO</div>}
            </button>
          );
        })}
      </div>
    </div>
  );
}
