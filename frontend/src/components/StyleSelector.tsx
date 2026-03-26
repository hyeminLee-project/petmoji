import type { EmojiStyle } from "@/types/api";

interface Props {
  style: EmojiStyle;
  onStyleChange: (style: EmojiStyle) => void;
}

export default function StyleSelector({ style, onStyleChange }: Props) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        캐릭터 스타일
      </label>
      <div className="grid grid-cols-2 gap-3">
        <button
          type="button"
          onClick={() => onStyleChange("2d")}
          className={`p-4 rounded-xl border-2 text-center transition-colors cursor-pointer ${
            style === "2d"
              ? "border-orange-400 bg-orange-50"
              : "border-gray-200 hover:border-gray-300"
          }`}
        >
          <div className="text-2xl mb-1">✏️</div>
          <div className="font-medium">2D 캐릭터</div>
          <div className="text-xs text-gray-500">카카오프렌즈 스타일</div>
        </button>
        <button
          type="button"
          onClick={() => onStyleChange("3d")}
          className={`p-4 rounded-xl border-2 text-center transition-colors cursor-pointer ${
            style === "3d"
              ? "border-orange-400 bg-orange-50"
              : "border-gray-200 hover:border-gray-300"
          }`}
        >
          <div className="text-2xl mb-1">🧸</div>
          <div className="font-medium">3D 캐릭터</div>
          <div className="text-xs text-gray-500">팝마트 피규어 스타일</div>
        </button>
      </div>
    </div>
  );
}
