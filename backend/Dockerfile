FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
# setuptools 업그레이드: 베이스 이미지 동봉 버전의 PYSEC-2026-3447 취약점 대응
RUN pip install --no-cache-dir --upgrade "setuptools>=83.0.0" \
    && pip install --no-cache-dir -r requirements.txt

COPY app/ app/

# non-root 유저로 실행
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
