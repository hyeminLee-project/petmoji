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

      const reader = res.body?.getReader();
      if (!reader) throw new Error("스트리밍을 지원하지 않는 응답입니다");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const events = buffer.split("\n\n");
        buffer = events.pop() || "";

        for (const eventStr of events) {
          if (!eventStr.trim()) continue;

          let eventType = "";
          let eventData = "";

          for (const line of eventStr.split("\n")) {
            if (line.startsWith("event: ")) eventType = line.slice(7);
            else if (line.startsWith("data: ")) eventData = line.slice(6);
          }

          if (!eventType || !eventData) continue;

          const data = JSON.parse(eventData);

          switch (eventType) {
            case "progress":
              callbacks.onProgress(data.message);
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
              callbacks.onError(new Error(data.message));
              break;
          }
        }
      }
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
