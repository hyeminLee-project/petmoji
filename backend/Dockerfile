FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

# non-root 유저로 실행
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

# --proxy-headers: Render 프록시가 붙이는 X-Forwarded-For에서 실제 클라이언트 IP를 읽음
#   (없으면 모든 요청이 프록시 IP로 집계되어 rate limit을 전체 사용자가 공유)
# --forwarded-allow-ips="*": 컨테이너의 유일한 유입 경로가 Render 프록시라 전체 신뢰 안전
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
