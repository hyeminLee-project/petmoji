"use client";

import Link from "next/link";
import { AgentChat } from "@/components/agent/AgentChat";

export default function AgentPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-amber-50 to-orange-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-orange-100 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="text-gray-400 hover:text-gray-600 transition-colors text-sm"
          >
            ← 홈
          </Link>
          <h1 className="text-lg font-bold text-gray-800">
            🤖 PetMoji Agent
          </h1>
        </div>
        <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded-full">
          AI 자율 생성
        </span>
      </header>

      {/* Chat */}
      <AgentChat />
    </div>
  );
}
