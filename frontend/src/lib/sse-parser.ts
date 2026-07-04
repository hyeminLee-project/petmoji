/**
 * SSE 응답 스트림을 읽어 이벤트별 콜백으로 전달하는 공통 파서.
 *
 * sse.ts / wizard-api.ts / agent-api.ts가 공유한다.
 * 이벤트 형식: "event: <type>\ndata: <json>\n\n"
 */
export async function readSSEStream(
  res: Response,
  onEvent: (type: string, data: unknown) => void
): Promise<void> {
  const reader = res.body?.getReader();
  if (!reader) throw new Error("스트리밍을 지원하지 않는 응답입니다");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // 더블 뉴라인으로 이벤트 구분, 마지막 조각은 다음 청크와 이어붙임
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
      onEvent(eventType, JSON.parse(eventData));
    }
  }
}
