"use client";

import { useCallback, useRef, useState, useEffect } from "react";
import { agentGenerate } from "@/lib/agent-api";
import { ChatMessage, type MessageType } from "./ChatMessage";

export function AgentChat() {
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string>("");
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selected = e.target.files?.[0];
      if (!selected || !selected.type.startsWith("image/")) return;
      setFile(selected);
      const url = URL.createObjectURL(selected);
      setFilePreview(url);
    },
    [],
  );

  const handleSubmit = useCallback(() => {
    if (!file || !prompt.trim() || loading) return;

    const userMsg: MessageType = {
      role: "user",
      text: prompt,
      imagePreview: filePreview,
    };

    setMessages((prev) => [...prev, userMsg]);
    setPrompt("");
    setLoading(true);

    const controller = agentGenerate(file, prompt, {
      onProgress: (message) => {
        setMessages((prev) => [...prev, { role: "agent", text: message }]);
      },
      onToolCall: (event) => {
        setMessages((prev) => [
          ...prev,
          { role: "tool_call", tool: event.tool, turn: event.turn },
        ]);
      },
      onToolResult: (event) => {
        setMessages((prev) => [
          ...prev,
          {
            role: "tool_result",
            tool: event.tool,
            success: event.success,
            turn: event.turn,
          },
        ]);
      },
      onComplete: (data) => {
        if (data.emojis.length > 0) {
          setMessages((prev) => [
            ...prev,
            { role: "emojis", emojis: data.emojis },
          ]);
        }
        if (data.summary) {
          setMessages((prev) => [
            ...prev,
            { role: "agent", text: data.summary },
          ]);
        }
        setLoading(false);
      },
      onError: (error) => {
        setMessages((prev) => [
          ...prev,
          { role: "error", text: error.message },
        ]);
        setLoading(false);
      },
    });

    abortRef.current = controller;
  }, [file, prompt, filePreview, loading]);

  const handleCancel = useCallback(() => {
    abortRef.current?.abort();
    setLoading(false);
    setMessages((prev) => [
      ...prev,
      { role: "error", text: "작업이 취소되었습니다" },
    ]);
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit],
  );

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 space-y-3">
            <span className="text-5xl">🐾</span>
            <p className="text-lg font-medium">반려동물 사진을 올리고</p>
            <p className="text-sm">
              자연어로 이모지를 요청해보세요
            </p>
            <div className="text-xs text-gray-300 space-y-1 mt-4 text-center">
              <p>&quot;카카오프렌즈 스타일로 8개 만들어줘&quot;</p>
              <p>&quot;리본 달고 수채화 느낌으로&quot;</p>
              <p>&quot;32개 풀세트 카카오 규격으로&quot;</p>
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}
        {loading && (
          <div className="flex justify-center">
            <div className="bg-gray-100 text-gray-500 text-sm px-3 py-1.5 rounded-full animate-pulse">
              Agent가 작업 중...
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-gray-200 bg-white px-4 py-3">
        {/* File preview */}
        {filePreview && (
          <div className="mb-2 flex items-center gap-2">
            <img
              src={filePreview}
              alt="미리보기"
              className="w-10 h-10 rounded-lg object-cover"
            />
            <span className="text-xs text-gray-500">{file?.name}</span>
            <button
              onClick={() => {
                setFile(null);
                setFilePreview("");
                if (fileInputRef.current) fileInputRef.current.value = "";
              }}
              className="text-xs text-red-400 hover:text-red-600"
            >
              삭제
            </button>
          </div>
        )}

        <div className="flex items-end gap-2">
          {/* Photo upload button */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="p-2.5 rounded-xl bg-gray-100 hover:bg-gray-200 transition-colors shrink-0"
            title="사진 첨부"
          >
            📷
          </button>

          {/* Text input */}
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              file
                ? "이모지를 어떻게 만들까요?"
                : "먼저 사진을 첨부해주세요"
            }
            disabled={!file}
            rows={1}
            className="flex-1 resize-none rounded-xl border border-gray-200 px-3 py-2.5 text-sm focus:outline-none focus:border-orange-400 disabled:bg-gray-50 disabled:text-gray-400"
          />

          {/* Send / Cancel button */}
          {loading ? (
            <button
              onClick={handleCancel}
              className="p-2.5 rounded-xl bg-red-500 hover:bg-red-600 text-white transition-colors shrink-0"
            >
              ■
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!file || !prompt.trim()}
              className="p-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white transition-colors shrink-0 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              ↑
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
