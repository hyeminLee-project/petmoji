import type { WizardStep } from "@/types/api";

const STEPS: { key: WizardStep; label: string }[] = [
  { key: "style", label: "스타일" },
  { key: "proportion", label: "비율" },
  { key: "detail", label: "세부" },
  { key: "reference", label: "레퍼런스" },
  { key: "scene", label: "장면" },
  { key: "generate", label: "생성" },
];

interface Props {
  currentStep: WizardStep;
  onStepClick?: (step: WizardStep) => void;
}

export default function StepIndicator({ currentStep, onStepClick }: Props) {
  const currentIndex = STEPS.findIndex((s) => s.key === currentStep);

  return (
    <div className="flex items-center justify-between mb-8">
      {STEPS.map((step, i) => {
        const isCompleted = i < currentIndex;
        const isCurrent = step.key === currentStep;

        return (
          <div key={step.key} className="flex items-center flex-1">
            <button
              onClick={() => isCompleted && onStepClick?.(step.key)}
              disabled={!isCompleted}
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                isCurrent
                  ? "bg-orange-500 text-white"
                  : isCompleted
                    ? "bg-orange-200 text-orange-700 cursor-pointer hover:bg-orange-300"
                    : "bg-gray-200 text-gray-400"
              }`}
            >
              {isCompleted ? "✓" : i + 1}
            </button>
            <span
              className={`ml-2 text-xs ${isCurrent ? "text-orange-600 font-medium" : "text-gray-400"}`}
            >
              {step.label}
            </span>
            {i < STEPS.length - 1 && (
              <div
                className={`flex-1 h-0.5 mx-3 ${isCompleted ? "bg-orange-200" : "bg-gray-200"}`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
