/** 이모지 미리보기 위에 얹는 캡션 텍스트 오버레이 (EmojiGrid / LoadingSpinner 공용) */

const SHADOW = {
  sm: "-1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff",
  md: "-2px -2px 0 #fff, 2px -2px 0 #fff, -2px 2px 0 #fff, 2px 2px 0 #fff, 0 -2px 0 #fff, 0 2px 0 #fff, -2px 0 0 #fff, 2px 0 0 #fff",
} as const;

interface Props {
  caption?: string;
  size?: keyof typeof SHADOW;
}

export default function CaptionBadge({ caption, size = "md" }: Props) {
  if (!caption) return null;

  return (
    <span
      className={`absolute left-0 right-0 text-center font-extrabold text-gray-900 leading-tight pointer-events-none ${
        size === "md" ? "top-1.5 text-base" : "top-1 text-xs"
      }`}
      style={{ textShadow: SHADOW[size] }}
    >
      {caption}
    </span>
  );
}
