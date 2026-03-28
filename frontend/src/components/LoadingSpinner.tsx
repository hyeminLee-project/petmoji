import type { EmojiResult } from "@/types/api";

interface Props {
  step?: string;
  message?: string;
  progress?: number;
  currentEmoji?: number;
  totalEmojis?: number;
  partialEmojis?: EmojiResult[];
}

export default function LoadingSpinner({
  step,
  message,
  progress = 0,
  currentEmoji,
  totalEmojis,
  partialEmojis = [],
}: Props) {
  const percentage = Math.round(progress * 100);

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
      {/* 진행률 바 */}
      <div className="w-full bg-gray-100 rounded-full h-2 mb-6">
        <div
          className="bg-orange-500 h-2 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* 단계 메시지 */}
      <div className="text-center mb-6">
        <div className="text-4xl mb-3">
          {step === "analyzing" && "🔍"}
          {step === "analyzed" && "✅"}
          {step === "generating" && "🎨"}
          {!step && "🎨"}
        </div>
        <h3 className="text-lg font-semibold text-gray-700 mb-1">
          {message || "이모지를 그리고 있어요..."}
        </h3>
        <p className="text-sm text-gray-400">
          {currentEmoji && totalEmojis
            ? `${currentEmoji} / ${totalEmojis}`
            : `${percentage}%`}
        </p>
      </div>

      {/* 실시간 이모지 미리보기 */}
      {partialEmojis.length > 0 && (
        <div className="grid grid-cols-4 gap-3 mt-4">
          {partialEmojis.map((emoji) => (
            <div
              key={emoji.emotion}
              className="bg-gray-50 rounded-lg p-2 text-center animate-fade-in"
            >
              <img
                src={emoji.image_url}
                alt={emoji.emotion}
                className="w-full aspect-square object-cover rounded-lg mb-1"
              />
              <p className="text-xs text-gray-500">{emoji.emotion}</p>
            </div>
          ))}
          {/* 아직 생성 안 된 슬롯 */}
          {totalEmojis &&
            Array.from({ length: totalEmojis - partialEmojis.length }).map(
              (_, i) => (
                <div
                  key={`placeholder-${i}`}
                  className="bg-gray-50 rounded-lg p-2 flex items-center justify-center aspect-square animate-pulse"
                >
                  <span className="text-2xl text-gray-300">?</span>
                </div>
              )
            )}
        </div>
      )}

      {/* 동물 이모지 애니메이션 (분석 단계) */}
      {!partialEmojis.length && (
        <div className="flex justify-center gap-2 mt-4">
          {["🐶", "🐱", "🐰", "🐹"].map((emoji, i) => (
            <span
              key={i}
              className="text-2xl animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }}
            >
              {emoji}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
