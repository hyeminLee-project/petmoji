import type { ImageProvider } from "@/types/api";

interface Props {
  provider: ImageProvider;
  onProviderChange: (provider: ImageProvider) => void;
}

export default function ProviderSelector({ provider, onProviderChange }: Props) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        AI 엔진
      </label>
      <div className="grid grid-cols-2 gap-3">
        <button
          type="button"
          onClick={() => onProviderChange("openai")}
          className={`p-4 rounded-xl border-2 text-center transition-colors cursor-pointer ${
            provider === "openai"
              ? "border-orange-400 bg-orange-50"
              : "border-gray-200 hover:border-gray-300"
          }`}
        >
          <div className="text-2xl mb-1">🤖</div>
          <div className="font-medium">GPT-4o</div>
          <div className="text-xs text-gray-500">2D 캐릭터에 강점</div>
        </button>
        <button
          type="button"
          onClick={() => onProviderChange("gemini")}
          className={`p-4 rounded-xl border-2 text-center transition-colors cursor-pointer ${
            provider === "gemini"
              ? "border-orange-400 bg-orange-50"
              : "border-gray-200 hover:border-gray-300"
          }`}
        >
          <div className="text-2xl mb-1">💎</div>
          <div className="font-medium">Gemini</div>
          <div className="text-xs text-gray-500">무료 티어 · 3D에 강점</div>
        </button>
      </div>
    </div>
  );
}
