import { readSSEStream } from "./sse-parser";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ToolCallEvent {
  tool: string;
  input: Record<string, unknown>;
  turn: number;
}

export interface ToolResultEvent {
  tool: string;
  success: boolean;
  turn: number;
}

export interface AgentCompleteEvent {
  summary: string;
  emojis: Array<{ emotion: string; image_url: string }>;
  converted?: Array<{ emotion: string; image_url: string }>;
}

export interface AgentStreamCallbacks {
  onProgress: (message: string) => void;
  onToolCall: (event: ToolCallEvent) => void;
  onToolResult: (event: ToolResultEvent) => void;
  onComplete: (data: AgentCompleteEvent) => void;
  onError: (error: Error) => void;
}

export function agentGenerate(
  file: File,
  prompt: string,
  callbacks: AgentStreamCallbacks,
): AbortController {
  const controller = new AbortController();

  const formData = new FormData();
  formData.append("file", file);
  formData.append("prompt", prompt);

  (async () => {
    try {
      const res = await fetch(`${API_BASE}/api/agent/generate`, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });

      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(`서버 오류 (${res.status}): ${text || "알 수 없는 오류"}`);
      }

      await readSSEStream(res, (eventType, data) => {
        switch (eventType) {
          case "progress":
            callbacks.onProgress((data as { message: string }).message);
            break;
          case "tool_call":
            callbacks.onToolCall(data as ToolCallEvent);
            break;
          case "tool_result":
            callbacks.onToolResult(data as ToolResultEvent);
            break;
          case "complete":
            callbacks.onComplete(data as AgentCompleteEvent);
            break;
          case "error":
            callbacks.onError(new Error((data as { message: string }).message));
            break;
        }
      });
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        callbacks.onError(
          err instanceof Error ? err : new Error("Agent 연결에 실패했습니다"),
        );
      }
    }
  })();

  return controller;
}
