/** 반려동물 특징 분석 결과 */
export interface PetFeatures {
  animal_type: string;
  breed: string;
  fur_color: string;
  fur_pattern: string;
  ear_shape: string;
  eye_color: string;
  eye_shape: string;
  nose_shape: string;
  body_shape: string;
  distinctive_features: string[];
  current_expression: string;
  overall_vibe: string;
}

/** 개별 이모지 결과 */
export interface EmojiResult {
  emotion: string;
  image_url: string;
}

/** 이모지 생성 API 응답 */
export interface GenerateResponse {
  pet_features: PetFeatures;
  emojis: EmojiResult[];
}

/** 이모지 스타일 */
export type EmojiStyle = "2d" | "3d" | "watercolor" | "pixel" | "realistic";

/** 티어 */
export type Tier = "free" | "premium" | "custom";

/** 위자드 단계 */
export type WizardStep = "style" | "proportion" | "detail" | "reference" | "generate";

/** 비율 */
export type Proportion = "chibi" | "normal" | "realistic";

/** 레퍼런스 */
export type Reference = "kakao" | "line" | "sanrio" | "popmart" | "none";

/** 세부 조정 */
export interface DetailOptions {
  eye_size: "big" | "normal" | "small";
  outline: "bold" | "normal" | "none";
  background: "white" | "transparent" | "gradient";
}

/** 위자드 세션 */
export interface WizardSession {
  session_id: string;
  session_token: string;
  pet_features: PetFeatures;
  tier_config: Record<string, unknown>;
}

/** AI 이미지 생성 provider */
export type ImageProvider = "openai" | "gemini";

/** 악세사리 */
export type Accessory =
  | "none" | "ribbon" | "bowtie" | "crown" | "flower" | "glasses"
  | "hat" | "scarf" | "bandana" | "headband";

/** 배경 */
export type Background =
  | "white" | "transparent" | "gradient"
  | "park" | "room" | "cafe" | "beach" | "snow" | "sky" | "night";

/** 시간대 */
export type TimeOfDay = "none" | "morning" | "afternoon" | "sunset" | "night";

/** 변환 포맷 */
export type ConvertFormat =
  | "kakao"
  | "kakao_animated"
  | "kakao_large_square"
  | "kakao_large_wide"
  | "kakao_large_tall"
  | "imessage"
  | "sticker"
  | "gif"
  | "wallpaper";

/** 변환된 이모지 */
export interface ConvertedEmoji {
  emotion: string;
  image_url: string;
  format: string;
  width: number;
  height: number;
}

/** 변환 API 응답 */
export interface ConvertResponse {
  format: string;
  emojis: ConvertedEmoji[];
}

/** 포맷 정보 */
export interface FormatInfo {
  id: ConvertFormat;
  name: string;
  size: string;
}
