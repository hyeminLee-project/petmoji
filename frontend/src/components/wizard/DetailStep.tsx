import type { DetailOptions } from "@/types/api";

interface Props {
  value: DetailOptions;
  onChange: (detail: DetailOptions) => void;
}

const OPTIONS = {
  eye_size: [
    { value: "big", label: "크게 👀" },
    { value: "normal", label: "보통 🙂" },
    { value: "small", label: "작게 😑" },
  ],
  outline: [
    { value: "bold", label: "두꺼운 선" },
    { value: "normal", label: "보통" },
    { value: "none", label: "없음" },
  ],
  background: [
    { value: "white", label: "흰색" },
    { value: "transparent", label: "투명" },
    { value: "gradient", label: "그라데이션" },
  ],
} as const;

export default function DetailStep({ value, onChange }: Props) {
  const update = (key: keyof DetailOptions, val: string) => {
    onChange({ ...value, [key]: val } as DetailOptions);
  };

  return (
    <div>
      <h3 className="text-lg font-bold text-gray-800 mb-4">Step 3. 세부 조정</h3>
      <div className="space-y-4">
        {(Object.entries(OPTIONS) as [keyof DetailOptions, typeof OPTIONS.eye_size][]).map(
          ([key, opts]) => (
            <div key={key}>
              <label className="block text-sm font-medium text-gray-600 mb-2">
                {key === "eye_size" ? "눈 크기" : key === "outline" ? "외곽선" : "배경"}
              </label>
              <div className="flex gap-2">
                {opts.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => update(key, opt.value)}
                    className={`flex-1 py-2 px-3 rounded-lg text-sm transition-colors cursor-pointer ${
                      value[key] === opt.value
                        ? "bg-orange-500 text-white"
                        : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          )
        )}
      </div>
    </div>
  );
}
