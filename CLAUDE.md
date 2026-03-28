# CLAUDE.md

## Git Commit Convention (Gitmoji)

모든 커밋 메시지는 gitmoji를 사용합니다.

### 형식

```
<gitmoji> <type>: <한줄 설명>

- 변경 내용 1
- 변경 내용 2

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
```

### Type

| type | 용도 |
|---|---|
| `feat` | 새 기능 |
| `fix` | 버그 수정 |
| `chore` | 설정, 빌드, 의존성 등 |
| `refactor` | 리팩토링 |
| `docs` | 문서 |
| `style` | UI/스타일 |
| `test` | 테스트 |

### Gitmoji 가이드

| 이모지 | 코드 | 용도 |
|---|---|---|
| 🎉 | `:tada:` | 프로젝트 초기 설정 |
| ✨ | `:sparkles:` | 새 기능 추가 |
| 🐛 | `:bug:` | 버그 수정 |
| 🔥 | `:fire:` | 코드/파일 삭제 |
| 🔧 | `:wrench:` | 설정 파일 변경 |
| ♻️ | `:recycle:` | 리팩토링 |
| 💄 | `:lipstick:` | UI/스타일 변경 |
| ✅ | `:white_check_mark:` | 테스트 추가/수정 |
| 📝 | `:memo:` | 문서 추가/수정 |
| 🚀 | `:rocket:` | 배포 관련 |
| ➕ | `:heavy_plus_sign:` | 의존성 추가 |
| ➖ | `:heavy_minus_sign:` | 의존성 제거 |
| 🔀 | `:twisted_rightwards_arrows:` | 브랜치 머지 |
| 🏗️ | `:building_construction:` | 아키텍처 변경 |
| 🗃️ | `:card_file_box:` | DB/스키마 변경 |
| 🔒 | `:lock:` | 보안 관련 |
| 🌐 | `:globe_with_meridians:` | 국제화/다국어 |
| 💡 | `:bulb:` | 주석 추가/수정 |
| 🚚 | `:truck:` | 파일/경로 이동 |
| 🎨 | `:art:` | 코드 구조/포맷 개선 |

### 예시

```
✨ feat: Add multi-format emoji converter

- kakao(360x360), imessage(408x408), sticker(512x512) 변환기 추가
- gif, wallpaper 변환기 추가
- POST /api/convert 엔드포인트 추가

🐛 fix: Fix Gemini model name for imagen API

- imagen-3.0 → imagen-4.0 모델명 업데이트

🔧 chore: Add VS Code project settings

- launch.json: 백엔드/프론트 디버그 설정
- tasks.json: 빌드/테스트 단축 작업
- extensions.json: 추천 확장 목록
```

## 브랜치 전략

- `main` — 안정 버전
- `feature/*` — 기능 개발
- `fix/*` — 버그 수정
- `chore/*` — 설정/문서 등
