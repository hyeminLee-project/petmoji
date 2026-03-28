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
export type EmojiStyle = "2d" | "3d";

/** AI 이미지 생성 provider */
export type ImageProvider = "openai" | "gemini";

/** 변환 포맷 */
export type ConvertFormat = "kakao" | "imessage" | "sticker" | "gif" | "wallpaper";

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
