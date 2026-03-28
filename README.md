<div align="center">

# 🐾 PetMoji

### AI Pet Character Emoji Generator

**Turn Your Pet Photo into Kakao-Style Character Emoji Set**

[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[Features](#-features) · [Getting Started](#-getting-started) · [Architecture](#-architecture) · [Commands](#-commands)

</div>

---

## 💡 Why PetMoji?

> _"My dog has the cutest expression... I wish I could turn it into a sticker!"_
>
> _"I want personalized emoji of my cat, not generic ones from the store."_

Every pet owner has felt this — your pet's unique personality deserves its own emoji set. But creating custom character stickers requires illustration skills and hours of work.

**PetMoji** analyzes your pet's physical features from a single photo, then generates a complete emoji set in Kakao Friends / LINE Friends style — with 8 emotions, multiple art styles, and platform-ready formats.

---

## ✨ Features

| Feature | Description |
|:---|:---|
| 📸 **One Photo Upload** | Drag & drop a pet photo, AI extracts 12 physical features |
| 🎨 **Dual Art Style** | 2D (Kakao Friends style) or 3D (Pop Mart figurine style) |
| 🤖 **Dual AI Engine** | Choose between GPT-4o or Gemini Imagen 4 |
| 😊 **8 Emotions** | Happy, sad, angry, sleepy, love, surprised, cool, celebrate |
| ✏️ **Custom Prompt** | Fine-tune with presets or free-form input |
| 📦 **5 Export Formats** | KakaoTalk (360px), iMessage (408px), Sticker PNG (512px), GIF, Phone Wallpaper |
| ⬇️ **Download** | Individual or bulk download |
| 🔒 **Rate Limited** | 10 requests/min per IP |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Frontend                           │
│              Next.js 16 + Tailwind v4                │
│                                                      │
│  ┌────────────┐ ┌─────────┐ ┌───────────────────┐   │
│  │   Photo    │ │  Style  │ │  Custom Prompt    │   │
│  │  Uploader  │ │ Selector│ │  (presets + free)  │   │
│  └─────┬──────┘ └────┬────┘ └────────┬──────────┘   │
│        └──────────────┼───────────────┘              │
│                       ▼                              │
│              POST /api/generate                      │
├──────────────────────────────────────────────────────┤
│                    Backend                            │
│               Python + FastAPI                        │
│                                                      │
│  ┌────────────────────────────────────────────┐      │
│  │  Step 1: Analyze (Claude Vision / Gemini)  │      │
│  │  → breed, fur color, ear shape, eye, etc.  │      │
│  └──────────────────┬─────────────────────────┘      │
│                     ▼                                │
│  ┌────────────────────────────────────────────┐      │
│  │  Step 2: Generate (GPT-4o / Gemini Imagen) │      │
│  │  → 8 emotion emojis per set                │      │
│  └──────────────────┬─────────────────────────┘      │
│                     ▼                                │
│  ┌────────────────────────────────────────────┐      │
│  │  Step 3: Convert (PIL)                     │      │
│  │  → kakao / imessage / sticker / gif / wall │      │
│  └────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

- [Python 3.11+](https://python.org/)
- [Node.js 18+](https://nodejs.org/)
- API Key: [OpenAI](https://platform.openai.com/api-keys) or [Google AI](https://aistudio.google.com/apikey)

### Installation

```bash
# Clone the repo
git clone https://github.com/hyeminLee-project/petmoji.git
cd petmoji

# Set up environment variables
cp backend/.env.example backend/.env
# Add your API keys to backend/.env

# Install dependencies
make install

# Start dev server
make dev
```

Open [http://localhost:3000](http://localhost:3000) and upload your pet photo!

### 🐳 Docker

```bash
cp backend/.env.example backend/.env
make docker-build
make docker-up
```

---

## 📋 Commands

| Command | Description |
|:---|:---|
| `make dev` | Start backend + frontend simultaneously |
| `make install` | Install all dependencies |
| `make build` | Production build (frontend) |
| `make test` | Run backend tests |
| `make lint` | Lint backend (Ruff) + frontend (ESLint) |
| `make format` | Auto-format all code |
| `make docker-up` | Run with Docker Compose |
| `make docker-down` | Stop Docker containers |
| `make clean` | Remove build artifacts |
| `make help` | Show all commands |

---

## 🛠️ Tech Stack

| Category | Technology |
|:---|:---|
| **Frontend** | Next.js 16 (App Router) · TypeScript · Tailwind CSS v4 |
| **Backend** | Python 3.11 · FastAPI · Pydantic |
| **AI Analysis** | Claude Vision · Gemini 2.5 Flash (selectable) |
| **AI Generation** | GPT-4o Image · Gemini Imagen 4 (selectable) |
| **Image Processing** | Pillow (PIL) |
| **Infrastructure** | Docker Compose · Makefile |
| **Security** | slowapi (rate limiting) · CORS · input validation |

---

## 🗂️ Project Structure

```
petmoji/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + CORS + rate limiting
│   │   ├── routers/
│   │   │   ├── emoji.py         # POST /api/generate
│   │   │   └── convert.py       # POST /api/convert, GET /api/formats
│   │   ├── services/
│   │   │   ├── analyzer.py      # Pet photo analysis (Claude/Gemini)
│   │   │   └── generator.py     # Emoji generation (GPT-4o/Gemini)
│   │   ├── converters/          # 5 format converters
│   │   │   ├── kakao.py         # 360x360
│   │   │   ├── imessage.py      # 408x408
│   │   │   ├── sticker.py       # 512x512 transparent
│   │   │   ├── gif.py           # 256x256 animated
│   │   │   └── wallpaper.py     # 1170x2532 pattern
│   │   └── models/schemas.py    # Pydantic schemas
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/page.tsx         # Main page
│   │   ├── components/          # UI components
│   │   ├── lib/api.ts           # API client
│   │   └── types/api.ts         # TypeScript types
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── Makefile
├── CLAUDE.md                    # Commit & PR conventions
└── README.md
```

---

## 🔧 Environment Variables

```bash
# Required (at least one AI engine)
OPENAI_API_KEY=your_key       # GPT-4o emoji generation
GOOGLE_API_KEY=your_key       # Gemini analysis + generation (free tier)

# Optional
ANTHROPIC_API_KEY=your_key    # Claude Vision analysis
CORS_ORIGINS=http://localhost:3000  # Add your domain for deployment
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit following [gitmoji convention](CLAUDE.md) (`✨ feat: Add amazing feature`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request following [PR convention](CLAUDE.md#pr-convention)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<div align="center">

**If PetMoji makes you smile, give it a ⭐!**

Made with ❤️ for pet lovers everywhere

</div>
