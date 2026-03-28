# CLAUDE.md

## Git Commit Convention (Gitmoji)

모든 커밋 메시지는 gitmoji를 사용합니다.

### 형식

```
<gitmoji> <type>: <한줄 설명> (영문, 50자 이내)

- 변경 내용 1 (한글 OK)
- 변경 내용 2
```

### 규칙

- 제목은 영문, 본문은 한글/영문 자유
- 제목에 마침표(.) 쓰지 않기
- 본문은 불렛(-) 리스트로 작성
- 하나의 커밋에는 하나의 기능/수정만
- Co-Authored-By 사용하지 않음

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

## PR Convention

### 제목

```
<gitmoji> <type>: <한줄 설명>
```

커밋 컨벤션과 동일. 예: `✨ feat: Add multi-format emoji converter`

### 본문

```markdown
## Summary
- 변경 사항 요약 (2~5줄)

## Changes
- [ ] 변경 파일/기능 체크리스트

## Test
- [ ] 테스트 통과 여부
- [ ] 수동 테스트 결과

## Screenshots
(UI 변경 시 스크린샷 첨부)
```

### PR 규칙

- 하나의 PR에는 하나의 기능/이슈
- `main`으로 직접 push 금지, 반드시 PR을 통해 머지
- CI(lint + build + test) 통과 필수
- PR 제목만으로 무슨 변경인지 알 수 있어야 함
- Draft PR: 작업 중일 때 `gh pr create --draft`

### 머지 전략

- **Squash and Merge** 사용 (커밋 히스토리 깔끔하게)
- 머지 후 feature 브랜치 삭제

## 보안

- `.env` 파일은 절대 커밋하지 않음 (`.gitignore`에 등록됨)
- API 키는 환경변수로만 관리
- 에러 메시지에 내부 정보 노출 금지
- 배포 시 HTTPS 필수
