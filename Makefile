.PHONY: dev dev-backend dev-frontend install install-backend install-frontend build test lint clean docker-up docker-down docker-build help

# ─── 개발 서버 ────────────────────────────────
dev: ## 백엔드 + 프론트엔드 동시 실행
	@make dev-backend & make dev-frontend

dev-backend: ## 백엔드 개발 서버 실행
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend: ## 프론트엔드 개발 서버 실행
	cd frontend && npm run dev

# ─── 설치 ─────────────────────────────────────
install: install-backend install-frontend ## 전체 의존성 설치

install-backend: ## 백엔드 의존성 설치
	cd backend && pip install -r requirements.txt

install-frontend: ## 프론트엔드 의존성 설치
	cd frontend && npm install

# ─── 빌드 ─────────────────────────────────────
build: ## 프론트엔드 프로덕션 빌드
	cd frontend && npm run build

# ─── 테스트 ────────────────────────────────────
test: ## 백엔드 테스트 실행
	cd backend && pytest -v

test-api: ## API 헬스체크
	@curl -s http://localhost:8000/health | python3 -m json.tool

# ─── 린트 ─────────────────────────────────────
lint: ## 전체 린트
	@make lint-backend && make lint-frontend

lint-backend: ## 백엔드 린트 (Ruff)
	cd backend && ruff check . && ruff format --check .

lint-frontend: ## 프론트엔드 린트 (ESLint)
	cd frontend && npm run lint

format: ## 전체 포맷팅
	cd backend && ruff format .
	cd frontend && npx prettier --write "src/**/*.{ts,tsx}"

# ─── Docker ────────────────────────────────────
docker-up: ## Docker 전체 실행
	docker compose up -d

docker-down: ## Docker 전체 중지
	docker compose down

docker-build: ## Docker 이미지 빌드
	docker compose build

docker-logs: ## Docker 로그 확인
	docker compose logs -f

# ─── 정리 ─────────────────────────────────────
clean: ## 빌드 산출물 정리
	rm -rf frontend/.next frontend/out
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

# ─── 도움말 ────────────────────────────────────
help: ## 사용 가능한 명령어 목록
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
