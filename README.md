# 🐾 PetMoji

반려동물 사진 한 장으로 카카오프렌즈/라인프렌즈 스타일의 캐릭터 이모지 세트를 자동 생성하는 서비스

## 기능

- **사진 업로드** — 드래그 앤 드롭으로 간편 업로드
- **AI 특징 추출** — Claude Vision 또는 Gemini Vision으로 반려동물 외형 분석
- **듀얼 AI 엔진** — GPT-4o / Gemini Imagen 선택 가능
- **캐릭터 이모지 생성** — 2D(카카오풍) / 3D(팝마트풍) 스타일 이모지 세트 (8종)
- **커스텀 프롬프트** — 프리셋 또는 자유 입력으로 스타일 미세 조정
- **다중 포맷 변환** — 카카오톡(360x360), iMessage(408x408), 스티커 PNG(512x512), GIF, 폰 배경화면
- **다운로드** — 개별 또는 전체 다운로드

## Tech Stack

| | 기술 |
|---|---|
| Frontend | Next.js 16 · TypeScript · Tailwind CSS v4 |
| Backend | Python · FastAPI |
| AI 분석 | Claude Vision · Gemini Vision (선택) |
| AI 생성 | GPT-4o Image · Gemini Imagen 4 (선택) |
| Infra | Docker Compose · Makefile |

## 실행 방법

### Quick Start (Makefile)

```bash
cp backend/.env.example backend/.env  # API 키 설정
make install                           # 전체 의존성 설치
make dev                               # 백엔드 + 프론트엔드 동시 실행
```

### Docker

```bash
cp backend/.env.example backend/.env  # API 키 설정
make docker-build                      # 이미지 빌드
make docker-up                         # 컨테이너 실행
```

### 수동 실행

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 환경 변수

```bash
# 필수 (최소 1개 AI 엔진)
OPENAI_API_KEY=your_key       # GPT-4o 이모지 생성
GOOGLE_API_KEY=your_key       # Gemini 분석 + 생성 (무료 티어)

# 선택
ANTHROPIC_API_KEY=your_key    # Claude Vision 분석
CORS_ORIGINS=http://localhost:3000  # 배포 시 도메인 추가
```

## 사용 가능한 명령어

```bash
make help  # 전체 명령어 확인
```
