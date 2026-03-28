import type { GenerateResponse, EmojiStyle, ImageProvider, ConvertFormat, ConvertResponse, EmojiResult, FormatInfo } from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * 반려동물 사진으로 이모지 세트 생성
 */
export async function generateEmojis(
  file: File,
  style: EmojiStyle = "2d",
  emojiCount: number = 8,
  provider: ImageProvider = "openai",
  customPrompt: string = ""
): Promise<GenerateResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("style", style);
  formData.append("emoji_count", String(emojiCount));
  formData.append("provider", provider);
  formData.append("custom_prompt", customPrompt);

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
 * 이모지를 특정 포맷으로 변환
 */
export async function convertEmojis(
  emojis: EmojiResult[],
  format: ConvertFormat
): Promise<ConvertResponse> {
  const res = await fetch(`${API_BASE}/api/convert`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ emojis, format }),
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "");
    throw new Error(`변환 오류 (${res.status}): ${errorText || "알 수 없는 오류"}`);
  }

  return res.json();
}

/**
 * 사용 가능한 포맷 목록 조회
 */
export async function getFormats(): Promise<FormatInfo[]> {
  const res = await fetch(`${API_BASE}/api/formats`);
  if (!res.ok) throw new Error("포맷 목록 조회 실패");
  const data = await res.json();
  return data.formats;
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
