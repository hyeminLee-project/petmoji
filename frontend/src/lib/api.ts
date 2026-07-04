import type { GenerateResponse, EmojiStyle, ImageProvider, ConvertFormat, ConvertResponse, ConvertedEmoji, EmojiResult, FormatInfo, Accessory, Background, TimeOfDay, Tier } from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * 반려동물 사진으로 이모지 세트 생성
 */
export async function generateEmojis(
  file: File,
  style: EmojiStyle = "2d",
  emojiCount: number = 8,
  provider: ImageProvider = "openai",
  customPrompt: string = "",
  accessory: Accessory = "none",
  background: Background = "white",
  timeOfDay: TimeOfDay = "none",
): Promise<GenerateResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("style", style);
  formData.append("emoji_count", String(emojiCount));
  formData.append("provider", provider);
  formData.append("custom_prompt", customPrompt);
  formData.append("accessory", accessory);
  formData.append("background", background);
  formData.append("time_of_day", timeOfDay);

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
 * 이모지 하나를 AI 영상 모델로 애니메이션화 (프리미엄 전용, 1~2분 소요)
 */
export async function animateEmoji(
  emoji: EmojiResult,
  tier: Tier
): Promise<ConvertedEmoji> {
  const res = await fetch(`${API_BASE}/api/animate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ emoji, tier }),
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "");
    let detail = "";
    try {
      detail = JSON.parse(errorText).detail;
    } catch {
      // JSON이 아니면 상태 코드 기반 메시지 사용
    }
    throw new Error(detail || `생성 오류 (${res.status})`);
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
