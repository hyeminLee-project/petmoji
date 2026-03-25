"use client";

import { useCallback, useRef, useState } from "react";

interface Props {
  onFileSelect: (file: File) => void;
  preview: string | null;
}

export default function PhotoUploader({ onFileSelect, preview }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = useCallback(
    (file: File) => {
      if (file.type.startsWith("image/")) {
        onFileSelect(file);
      }
    },
    [onFileSelect]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
        isDragging
          ? "border-orange-400 bg-orange-50"
          : "border-gray-300 hover:border-orange-300"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />

      {preview ? (
        <div className="flex flex-col items-center gap-4">
          <img
            src={preview}
            alt="Pet preview"
            className="w-48 h-48 object-cover rounded-xl"
          />
          <p className="text-sm text-gray-500">
            클릭하거나 드래그해서 다른 사진으로 변경
          </p>
        </div>
      ) : (
        <div className="py-8">
          <div className="text-5xl mb-4">📸</div>
          <p className="text-lg text-gray-600 font-medium">
            반려동물 사진을 업로드하세요
          </p>
          <p className="text-sm text-gray-400 mt-2">
            클릭 또는 드래그 앤 드롭 · JPG, PNG
          </p>
        </div>
      )}
    </div>
  );
}
