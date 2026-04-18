import type { EmojiResult } from "@/types/api";

const EMOTION_LABELS: Record<string, string> = {
  happy: "행복 😊",
  sad: "슬픔 😢",
  angry: "화남 😡",
  sleepy: "졸림 😴",
  love: "사랑 💕",
  surprised: "놀람 😲",
  cool: "멋짐 😎",
  celebrate: "축하 🎉",
  thumbsup: "좋아 👍",
  thumbsdown: "싫어 👎",
  grateful: "고마워 🙏",
  sorry: "미안 🙇",
  fighting: "화이팅 💪",
  tired: "지침 😩",
  hungry: "배고파 🍽️",
  eating: "냠냠 😋",
  laughing: "빵터짐 🤣",
  crying: "엉엉 😭",
  shy: "부끄 🫣",
  nervous: "떨림 😰",
  bored: "심심 😐",
  excited: "신남 🤩",
  confused: "멘붕 😵",
  sick: "아파 🤒",
  hot: "더워 🥵",
  cold: "추워 🥶",
  working: "작업중 💻",
  sleeping: "쿨쿨 😴",
  greeting: "안녕 👋",
  bye: "잘가 👋",
  running: "도망 🏃",
  hugging: "안아줘 🤗",
};

interface Props {
  emojis: EmojiResult[];
}

export default function EmojiGrid({ emojis }: Props) {
  const handleDownload = async (emoji: EmojiResult) => {
    const res = await fetch(emoji.image_url);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `petmoji-${emoji.emotion}.png`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadAll = async () => {
    for (const emoji of emojis) {
      await handleDownload(emoji);
    }
  };

  return (
    <div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        {emojis.map((emoji) => (
          <div
            key={emoji.emotion}
            className="group relative bg-gray-50 rounded-xl p-3 text-center"
          >
            <img
              src={emoji.image_url}
              alt={emoji.emotion}
              className="w-full aspect-square object-cover rounded-lg mb-2"
            />
            <p className="text-sm font-medium text-gray-700">
              {EMOTION_LABELS[emoji.emotion] || emoji.emotion}
            </p>
            <button
              onClick={() => handleDownload(emoji)}
              className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 bg-white/80 rounded-full p-1.5 text-xs transition-opacity cursor-pointer"
            >
              ⬇️
            </button>
          </div>
        ))}
      </div>

      <button
        onClick={handleDownloadAll}
        className="w-full py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-xl transition-colors cursor-pointer"
      >
        📦 전체 다운로드
      </button>
    </div>
  );
}
