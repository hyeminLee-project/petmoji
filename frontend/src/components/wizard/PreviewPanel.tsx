interface Props {
  imageUrl: string | null;
  loading: boolean;
  message?: string;
}

export default function PreviewPanel({ imageUrl, loading, message }: Props) {
  return (
    <div className="bg-gray-50 rounded-xl p-4 flex flex-col items-center justify-center min-h-[300px]">
      {loading ? (
        <div className="text-center">
          <div className="animate-spin text-3xl mb-3">🎨</div>
          <p className="text-sm text-gray-500">{message || "미리보기 생성 중..."}</p>
        </div>
      ) : imageUrl ? (
        <img
          src={imageUrl}
          alt="미리보기"
          className="max-w-full max-h-[280px] rounded-lg"
        />
      ) : (
        <div className="text-center text-gray-400">
          <div className="text-4xl mb-2">🖼️</div>
          <p className="text-sm">옵션을 선택하면 미리보기가 표시됩니다</p>
        </div>
      )}
    </div>
  );
}
