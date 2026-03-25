export default function LoadingSpinner() {
  return (
    <div className="bg-white rounded-2xl shadow-lg p-12 mb-8 text-center">
      <div className="animate-bounce text-6xl mb-4">🎨</div>
      <h3 className="text-xl font-semibold text-gray-700 mb-2">
        이모지를 그리고 있어요...
      </h3>
      <p className="text-gray-500">
        반려동물의 특징을 분석하고 캐릭터를 만드는 중입니다
      </p>
      <div className="mt-6 flex justify-center gap-2">
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
    </div>
  );
}
