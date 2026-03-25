# 🐾 PetMoji

반려동물 사진 한 장으로 카카오프렌즈/라인프렌즈 스타일의 캐릭터 이모지 세트를 자동 생성하는 서비스

## 기능

- **사진 업로드** — 드래그 앤 드롭으로 간편 업로드
- **AI 특징 추출** — Claude Vision으로 반려동물의 외형 특징 분석
- **캐릭터 이모지 생성** — GPT-4o로 2D/3D 스타일 이모지 세트 생성 (8종)
- **다운로드** — 개별 또는 전체 다운로드

## Tech Stack

| | 기술 |
|---|---|
| Frontend | Next.js 16 · TypeScript · Tailwind CSS v4 |
| Backend | Python · FastAPI |
| AI | Claude Vision (특징 분석) · GPT-4o Image (이모지 생성) |

## 실행 방법

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # API 키 설정
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 환경 변수

```
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
```
