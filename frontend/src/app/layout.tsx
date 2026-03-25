import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PetMoji - AI 반려동물 이모지 생성기",
  description:
    "반려동물 사진을 업로드하면 카카오프렌즈 스타일의 캐릭터 이모지 세트를 만들어드립니다",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-gradient-to-b from-amber-50 to-orange-50">
        {children}
      </body>
    </html>
  );
}
