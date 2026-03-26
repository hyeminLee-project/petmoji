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
