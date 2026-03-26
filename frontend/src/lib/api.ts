import type { GenerateResponse, EmojiStyle } from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * 반려동물 사진으로 이모지 세트 생성
 */
export async function generateEmojis(
  file: File,
  style: EmojiStyle = "2d",
  emojiCount: number = 8
): Promise<GenerateResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("style", style);
  formData.append("emoji_count", String(emojiCount));

  const res = await fetch(`${API_BASE}/api/generate`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "");
    throw new Error(`서버 오류 (${res.status}): ${errorText || "알 수 없는 오류"}`);
  }

  return res.json();
}

/**
 * 헬스체크
 */
export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
