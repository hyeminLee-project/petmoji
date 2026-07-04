"use client";

export type MessageType =
  | { role: "user"; text: string; imagePreview?: string }
  | { role: "agent"; text: string }
  | { role: "tool_call"; tool: string; turn: number }
  | { role: "tool_result"; tool: string; success: boolean; turn: number }
  | { role: "emojis"; emojis: Array<{ emotion: string; image_url: string }> }
  | { role: "error"; text: string };

const TOOL_LABELS: Record<string, string> = {
  analyze_pet: "사진 분석",
  generate_emojis: "이모지 생성",
  convert_kakao: "카카오 변환",
};

const TOOL_ICONS: Record<string, string> = {
  analyze_pet: "🔍",
  generate_emojis: "🎨",
  convert_kakao: "💬",
};

export function ChatMessage({ message }: { message: MessageType }) {
  switch (message.role) {
    case "user":
      return (
        <div className="flex justify-end">
          <div className="max-w-[80%] space-y-2">
            {message.imagePreview && (
              <img
                src={message.imagePreview}
                alt="업로드한 사진"
                className="w-32 h-32 object-cover rounded-xl ml-auto"
              />
            )}
            <div className="bg-orange-500 text-white px-4 py-2.5 rounded-2xl rounded-br-md">
              {message.text}
            </div>
          </div>
        </div>
      );

    case "agent":
      return (
        <div className="flex justify-start">
          <div className="max-w-[80%]">
            <div className="text-xs text-gray-400 mb-1">PetMoji Agent</div>
            <div className="bg-white px-4 py-2.5 rounded-2xl rounded-bl-md shadow-sm whitespace-pre-wrap">
              {message.text}
            </div>
          </div>
        </div>
      );

    case "tool_call":
      return (
        <div className="flex justify-center">
          <div className="bg-blue-50 text-blue-600 text-sm px-3 py-1.5 rounded-full flex items-center gap-1.5">
            <span className="animate-spin inline-block">
              {TOOL_ICONS[message.tool] || "⚙️"}
            </span>
            {TOOL_LABELS[message.tool] || message.tool} 실행 중...
          </div>
        </div>
      );

    case "tool_result":
      return (
        <div className="flex justify-center">
          <div
            className={`text-sm px-3 py-1.5 rounded-full ${
              message.success
                ? "bg-green-50 text-green-600"
                : "bg-red-50 text-red-600"
            }`}
          >
            {message.success ? "✅" : "❌"}{" "}
            {TOOL_LABELS[message.tool] || message.tool}{" "}
            {message.success ? "완료" : "실패"}
          </div>
        </div>
      );

    case "emojis":
      return (
        <div className="flex justify-start">
          <div className="max-w-[90%]">
            <div className="text-xs text-gray-400 mb-1">생성된 이모지</div>
            <div className="grid grid-cols-4 sm:grid-cols-8 gap-2 bg-white p-3 rounded-2xl shadow-sm">
              {message.emojis.map((emoji) => (
                <div key={emoji.emotion} className="text-center">
                  <img
                    src={emoji.image_url}
                    alt={emoji.emotion}
                    className="w-16 h-16 rounded-lg"
                  />
                  <span className="text-[10px] text-gray-500 mt-0.5 block truncate">
                    {emoji.emotion}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      );

    case "error":
      return (
        <div className="flex justify-center">
          <div className="bg-red-50 text-red-600 text-sm px-4 py-2 rounded-xl">
            {message.text}
          </div>
        </div>
      );
  }
}
