# PetMoji

반려동물 사진 한 장으로 나만의 캐릭터 이모지 세트를 AI로 자동 생성하는 서비스.

카카오프렌즈, 라인프렌즈, 산리오, 팝마트 스타일까지 선택하고, 악세사리/배경/시간대를 커스터마이징하여 최대 32종 감정 이모지 세트를 만들 수 있습니다. 한국어 캡션 자동 오버레이와 카카오 이모티콘 스토어 제안용 패키지(ZIP) 내보내기도 지원합니다.

## 주요 기능

### 티어 시스템

| | Free | Premium | Custom |
|---|---|---|---|
| 스타일 | 2D, 3D | 5종 전체 | 5종 전체 |
| 감정 이모지 | 4종 | 32종 | 32종 |
| 위자드 가이드 | X | O | O |
| 커스텀 프롬프트 | X | X | O |
| 악세사리/배경/시간대 | 제한적 | 전체 | 전체 |
| 변환 포맷 | PNG | 9종 전체 | 9종 전체 |
| 재생성 | 1회 | 3회 | 무제한 |

### Free 플로우
- 사진 업로드 (드래그 앤 드롭)
- AI 반려동물 외형 분석 (Gemini Vision / Claude Vision)
- 2D/3D 스타일 선택
- 4종 감정 이모지 자동 생성

### Premium/Custom 위자드 (6단계)

| 단계 | 설명 |
|---|---|
| 1. 스타일 | 2D, 3D, 수채화, 픽셀, 리얼리스틱 (5종) |
| 2. 비율 | 치비, 노멀, 리얼리스틱 |
| 3. 세부 조정 | 눈 크기 (big/normal/small), 외곽선 (bold/normal/none), 배경 (white/transparent/gradient) |
| 4. 레퍼런스 | 카카오, 라인, 산리오, 팝마트, 없음 |
| 5. 장면 설정 | 악세사리 (10종), 장면 배경 (10종), 시간대 (5종) |
| 6. 생성 | 최대 32종 감정 이모지 세트 생성 |

각 단계마다 AI 미리보기가 생성되어 결과를 확인하면서 진행할 수 있습니다.

### 감정 이모지 (32종)

**기본 8종:** happy, sad, angry, sleepy, love, surprised, cool, celebrate

**확장 24종:** thumbsup, thumbsdown, grateful, sorry, fighting, tired, hungry, eating, laughing, crying, shy, nervous, bored, excited, confused, sick, hot, cold, working, sleeping, greeting, bye, running, hugging

### 공통 기능
- 듀얼 AI 엔진: GPT Image (`gpt-image-1`) / Gemini Imagen 4 (`imagen-4.0-generate-001`) 선택
- 한국어 캡션 자동 생성 및 이미지 오버레이
- 다중 포맷 변환 (9종):

| 포맷 | 크기 | 비고 |
|---|---|---|
| kakao | 360x360 | 멈춰있는 이모티콘, 150KB 제한 |
| kakao_animated | 360x360 | 움직이는 이모티콘, 650KB 제한 |
| kakao_large_square | 540x540 | 큰 이모티콘 (정사각형), 1MB 제한 |
| kakao_large_wide | 540x300 | 큰 이모티콘 (가로형), 1MB 제한 |
| kakao_large_tall | 300x540 | 큰 이모티콘 (세로형), 1MB 제한 |
| imessage | 408x408 | iMessage 스티커 |
| sticker | 512x512 | 투명 배경 PNG |
| gif | 256x256 | 애니메이션 GIF |
| wallpaper | 1170x2532 | 폰 배경화면 |

- 카카오 이모티콘 제안 패키지: 이모티콘 32개 + 아이콘(78x78) + 공유이미지(600x166) ZIP
- 개별/전체 다운로드
- SSE 기반 실시간 생성 스트리밍

## 아키텍처

```
Frontend (Next.js 16)          Backend (FastAPI)
========================       ========================
page.tsx                       /api/generate
  +-- PhotoUploader              +-- analyze_pet_photo()
  +-- TierSelector               +-- generate_emoji_set()
  +-- ProviderSelector
  +-- StyleSelector            /api/generate/stream
  +-- CustomPrompt               +-- SSE 스트리밍 생성
  +-- EmojiGrid
  +-- FormatSelector           /api/wizard/start
  +-- SceneSelector              +-- LangGraph (analyze)
  +-- WizardContainer
      +-- StyleStep            /api/wizard/step
      +-- ProportionStep         +-- style_node()
      +-- DetailStep             +-- proportion_node()
      +-- ReferenceStep          +-- detail_node()
      +-- SceneStep              +-- reference_node()
      +-- PreviewPanel           +-- scene_node()
      +-- StepIndicator
                               /api/wizard/back
                                 +-- 이전 단계 복귀

                               /api/wizard/generate
                                 +-- generate_node()
                                 +-- 32 emotions x AI image
                                 +-- 한국어 캡션 오버레이

                               /api/convert
                                 +-- 9종 포맷 변환
                                 +-- kakao_submission (ZIP)

                               /api/formats
                                 +-- 지원 포맷 목록

                               /health
                                 +-- 헬스체크
```

### 위자드 상태 관리

LangGraph의 `StateGraph`와 SQLite 체크포인터를 사용하여 위자드 세션 상태를 관리합니다. 각 단계의 선택값과 미리보기 이미지가 세션에 누적 저장됩니다.

- 세션 TTL: 30분
- HMAC-SHA256 기반 세션 토큰 인증
- 5분 주기 만료 세션 자동 정리

## Tech Stack

| 영역 | 기술 |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript 6, Tailwind CSS v4 |
| Backend | Python 3.11+, FastAPI, LangGraph |
| AI 분석 | Gemini Vision (`gemini-2.5-flash`), Claude Vision (`claude-sonnet-4-20250514`) |
| AI 생성 | GPT Image (`gpt-image-1`), Gemini Imagen 4 (`imagen-4.0-generate-001`) |
| Rate Limiting | slowapi |
| 인프라 | Docker Compose, Render |

## 실행 방법

### Quick Start

```bash
# 1. 환경 변수 설정
cat > backend/.env << 'EOF'
GOOGLE_API_KEY=your_key       # Gemini 분석 + 생성
OPENAI_API_KEY=your_key       # GPT Image 생성 (선택)
ANTHROPIC_API_KEY=your_key    # Claude Vision 분석 (선택)
EOF

# 2. 의존성 설치 + 실행
make install
make dev
```

### Docker

```bash
make docker-build
make docker-up
```

### 접속

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 환경 변수

| 변수 | 필수 | 설명 |
|---|---|---|
| `GOOGLE_API_KEY` | O | Gemini Vision 분석 + Imagen 생성 |
| `OPENAI_API_KEY` | - | GPT Image 생성 (선택) |
| `ANTHROPIC_API_KEY` | - | Claude Vision 분석 (선택) |
| `CORS_ORIGINS` | - | 허용 도메인 (기본: localhost:3000,3001) |
| `ENVIRONMENT` | - | `production` 설정 시 HSTS 헤더 활성화 |

최소 1개 AI 엔진 키가 필요합니다. Gemini 키만 있으면 분석+생성 모두 가능합니다.

## 프로젝트 구조

```
petmoji/
+-- frontend/
|   +-- src/
|       +-- app/page.tsx              # 메인 페이지
|       +-- components/               # 공통 컴포넌트
|       +-- components/wizard/        # 위자드 6단계 컴포넌트
|       +-- lib/sse.ts                # SSE 스트리밍 클라이언트
|       +-- lib/wizard-api.ts         # 위자드 API 클라이언트
|       +-- types/api.ts              # 타입 정의
+-- backend/
|   +-- app/
|       +-- routers/                  # API 엔드포인트
|       +-- graph/                    # LangGraph 위자드
|       |   +-- wizard.py             # 그래프 정의
|       |   +-- nodes.py             # 노드 함수 (미리보기/생성)
|       |   +-- prompts.py           # 프롬프트 빌더
|       |   +-- state.py             # 위자드 상태 스키마
|       |   +-- callbacks.py         # SSE 콜백
|       +-- services/                 # AI 분석/생성/캡션 서비스
|       +-- converters/               # 포맷 변환기 (9종)
|       +-- models/                   # 티어, 감정 등 데이터 모델
|       +-- utils/                    # 업로드 검증 등
+-- docker-compose.yml
+-- Makefile
```

## 명령어

```bash
make help            # 전체 명령어 확인
make dev             # 개발 서버 실행 (백엔드 + 프론트)
make dev-backend     # 백엔드만 실행
make dev-frontend    # 프론트엔드만 실행
make install         # 전체 의존성 설치
make build           # 프론트엔드 프로덕션 빌드
make test            # 백엔드 테스트
make test-api        # API 헬스체크
make lint            # 린트 (ruff + eslint)
make format          # 포맷팅 (ruff + prettier)
make docker-up       # Docker 실행
make docker-down     # Docker 중지
make docker-build    # Docker 빌드
make docker-logs     # Docker 로그
make clean           # 캐시 정리
```
