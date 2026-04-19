# PetMoji

반려동물 사진 한 장으로 나만의 캐릭터 이모지 세트를 AI로 자동 생성하는 서비스.

카카오프렌즈, 라인프렌즈, 산리오, 팝마트 스타일까지 선택하고, 악세사리/배경/시간대를 커스터마이징하여 최대 32종 감정 이모지 세트를 만들 수 있습니다. 카카오 이모티콘 스토어 제안용 패키지(ZIP) 내보내기도 지원합니다.

## 주요 기능

### 무료 플로우
- 사진 업로드 (드래그 앤 드롭)
- AI 반려동물 외형 분석 (Gemini Vision)
- 2D/3D 스타일 선택
- 커스텀 프롬프트 입력
- 4종 이모지 자동 생성

### 프리미엄/커스텀 위자드 (6단계)

| 단계 | 설명 |
|---|---|
| 1. 스타일 | 2D, 3D, 수채화, 픽셀, 리얼리스틱 (5종) |
| 2. 비율 | 치비, 노멀, 리얼리스틱 |
| 3. 세부 조정 | 눈 크기, 외곽선, 배경 |
| 4. 레퍼런스 | 카카오, 라인, 산리오, 팝마트 |
| 5. 장면 설정 | 악세사리 (10종), 장면 배경 (8종), 시간대 (5종) |
| 6. 생성 | 최대 32종 감정 이모지 세트 생성 |

각 단계마다 AI 미리보기가 생성되어 결과를 확인하면서 진행할 수 있습니다.

### 공통 기능
- 듀얼 AI 엔진: GPT-4o / Gemini Imagen 선택
- 다중 포맷 변환: 카카오톡(360x360), iMessage(408x408), 스티커 PNG(512x512), GIF, 배경화면
- 카카오 이모티콘 제안 패키지: 이모티콘 32개 + 아이콘(78x78) + 공유이미지(600x166) ZIP
- 개별/전체 다운로드
- SSE 기반 실시간 생성 스트리밍

## 아키텍처

```
Frontend (Next.js 16)          Backend (FastAPI)
========================       ========================
page.tsx                       /api/generate/stream
  +-- PhotoUploader              +-- analyze_pet_photo()
  +-- TierSelector               +-- generate_emoji_set()
  +-- StyleSelector
  +-- WizardContainer          /api/wizard/start
      +-- StyleStep              +-- LangGraph (analyze)
      +-- ProportionStep
      +-- DetailStep           /api/wizard/step
      +-- ReferenceStep          +-- style_node()
      +-- SceneStep              +-- proportion_node()
      +-- PreviewPanel           +-- detail_node()
  +-- EmojiGrid                  +-- reference_node()
  +-- FormatSelector             +-- scene_node()

                               /api/wizard/generate
                                 +-- generate_node()
                                 +-- 32 emotions x AI image

                               /api/convert
                                 +-- kakao, imessage, sticker
                                 +-- gif, wallpaper
                                 +-- kakao_submission (ZIP)
```

### 위자드 상태 관리

LangGraph의 `StateGraph`와 SQLite 체크포인터를 사용하여 위자드 세션 상태를 관리합니다. 각 단계의 선택값과 미리보기 이미지가 세션에 누적 저장됩니다.

## Tech Stack

| 영역 | 기술 |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4 |
| Backend | Python, FastAPI, LangGraph |
| AI 분석 | Gemini Vision, Claude Vision (선택) |
| AI 생성 | GPT-4o Image, Gemini Imagen 4 (선택) |
| 인프라 | Docker Compose, Render |

## 실행 방법

### Quick Start

```bash
# 1. 환경 변수 설정
cat > backend/.env << 'EOF'
GOOGLE_API_KEY=your_key       # Gemini 분석 + 생성
OPENAI_API_KEY=your_key       # GPT-4o 이모지 생성 (선택)
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
| `OPENAI_API_KEY` | - | GPT-4o 이모지 생성 (선택) |
| `ANTHROPIC_API_KEY` | - | Claude Vision 분석 (선택) |
| `CORS_ORIGINS` | - | 배포 시 허용 도메인 (기본: localhost:3000) |

최소 1개 AI 엔진 키가 필요합니다. Gemini 키만 있으면 분석+생성 모두 가능합니다.

## 프로젝트 구조

```
petmoji/
+-- frontend/
|   +-- src/
|       +-- app/page.tsx              # 메인 페이지
|       +-- components/wizard/        # 위자드 6단계 컴포넌트
|       +-- lib/sse.ts                # SSE 스트리밍 클라이언트
|       +-- lib/wizard-api.ts         # 위자드 API 클라이언트
|       +-- types/api.ts              # 타입 정의
+-- backend/
|   +-- app/
|       +-- routers/                  # API 엔드포인트
|       +-- graph/                    # LangGraph 위자드
|       |   +-- wizard.py             # 그래프 정의
|       |   +-- nodes.py              # 노드 함수 (미리보기/생성)
|       |   +-- prompts.py            # 프롬프트 빌더
|       |   +-- state.py              # 위자드 상태 스키마
|       +-- services/                 # AI 분석/생성 서비스
|       +-- utils/                    # 업로드 검증 등
+-- docker-compose.yml
+-- Makefile
```

## 명령어

```bash
make help          # 전체 명령어 확인
make dev           # 개발 서버 실행
make test          # 테스트 실행
make lint          # 린트 실행
make docker-up     # Docker 실행
make docker-down   # Docker 중지
```
