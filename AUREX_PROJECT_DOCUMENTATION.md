# FLOWSPACE — Complete Project Documentation

> A premium AI-powered desktop productivity workspace built with Python, CustomTkinter, and a modular service architecture. Designed to function as an all-in-one AI assistant, content intelligence tool, creative studio, and personal productivity system.

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Tech Stack & Architecture](#2-tech-stack--architecture)
3. [Core Infrastructure](#3-core-infrastructure)
4. [Features — Detailed Breakdown](#4-features--detailed-breakdown)
   - [Dashboard](#41-dashboard)
   - [FLOWSPACE AI (Assistant)](#42-flowspace-ai-assistant)
   - [AI Planner](#43-ai-planner)
   - [Summarizer (Knowledge Base)](#44-summarizer-knowledge-base)
   - [Image Studio](#45-image-studio)
   - [File Converter](#46-file-converter)
   - [History](#47-history)
   - [Accounts](#48-accounts)
   - [Settings](#49-settings)
5. [API & Provider System](#5-api--provider-system)
6. [Database Schema](#6-database-schema)
7. [Known Limitations & Notes](#7-known-limitations--notes)

---

## 1. Project Overview

**FLOWSPACE** is a standalone desktop application that puts multiple AI-powered tools into a single unified dark-themed workspace. It connects to any OpenAI-compatible AI provider (NVIDIA NIM, Groq, OpenAI, GitHub Models, HuggingFace) using a single API key stored in a `.env` file.

**Why FLOWSPACE?**
- No browser needed — runs as a native desktop app
- One key for all features — no per-feature API setup
- Privacy-first — all data is stored locally in SQLite
- Extensible — adding new AI providers requires changing only one service file

---

## 2. Tech Stack & Architecture

| Layer | Technology |
|---|---|
| **UI Framework** | CustomTkinter (Python) — dark glassmorphism theme |
| **AI Backend** | OpenAI-compatible REST API (provider-agnostic) |
| **Image Generation** | NVIDIA NIM — `flux.2-klein-4b` model |
| **Embeddings / Search** | `sentence-transformers` (local, no cloud) |
| **Database** | SQLite (local file, no server) |
| **Audio Input** | `speech_recognition` + Google Speech API |
| **File Processing** | `pypdf`, `python-docx`, `pdfplumber`, `pytube` |
| **Event System** | Custom in-process publish/subscribe event bus |

### Architecture Pattern

```
main.py
  └── AurexApp (ui/app.py)
        ├── Sidebar Navigation
        ├── Views (ui/views/*.py)   ← one per feature
        │     └── Each view subscribes to events from services
        └── Services (services/*.py)
              ├── api_service.py    ← single API client for all LLM calls
              ├── event_bus.py      ← decoupled pub/sub between UI and services
              ├── ai_service.py     ← chat, intent routing
              ├── image_service.py  ← image generation pipeline
              ├── knowledge_pipeline.py  ← document ingestion pipeline
              └── task_service.py   ← task/planner management
```

---

## 3. Core Infrastructure

### `services/api_service.py` — Universal AI Client
**What it does:** Auto-detects which AI provider you're using by inspecting the API key format, then creates a single OpenAI-compatible client that every other service uses.

| Key Prefix | Provider Detected | Model Used |
|---|---|---|
| `nvapi-` | NVIDIA NIM | `meta/llama-3.1-8b-instruct` |
| `gsk_` | Groq | `llama-3.1-8b-instant` |
| `sk-` | OpenAI | `gpt-4o-mini` |
| `github_pat_` | GitHub Models | `gpt-4o-mini` |
| `hf_` | HuggingFace | `Meta-Llama-3-8B-Instruct` |

**Why:** Instead of each feature needing its own API integration, one service handles authentication for the whole app. Switching AI providers is a one-line change in `.env`.

### `services/event_bus.py` — Event System
**What it does:** A simple publish/subscribe message broker running inside the process. Services publish events (e.g., `IMAGE_GEN_SUCCESS`) and UI views subscribe to them to update without direct coupling.

**Why:** Keeps background threads (generation, processing) completely separate from UI code. The service doesn't know or care about the UI; it just fires events.

### `database/database.py` — SQLite Local Storage
**What it does:** All user data — chat history, generated images, tasks, knowledge base entries, sessions — stored in a single local SQLite `.db` file.

**Why:** No cloud database required. Data is private and works offline.

### `authentication/session.py` — Session Management
**What it does:** Tracks the currently logged-in user ID throughout the app lifetime. Used by all services to scope data queries to the current user.

---

## 4. Features — Detailed Breakdown

---

### 4.1 Dashboard

**File:** `ui/dashboard.py`

**What it does:** The home screen shown when FLOWSPACE starts. Provides a quick overview of:
- Recent AI chat sessions
- Recent generated images
- Quick-access buttons to each feature

**Why:** Gives users a glanceable summary of their workspace activity without navigating into each section.

---

### 4.2 FLOWSPACE AI (Assistant)

**Files:** `ui/views/assistant_view.py`, `services/ai_service.py`

**What it does:** A full-featured AI chat interface with session memory, command routing, and voice input.

#### Sub-features:

| Feature | How it works |
|---|---|
| **Persistent chat sessions** | Each conversation is a session stored in SQLite. Sessions are listed in the right sidebar and can be resumed at any time. |
| **Auto-title generation** | After the first message, the AI automatically generates a short descriptive title for the session. |
| **Intent-based command routing** | The AI classifies each message into an intent (e.g., `create_task`, `open_image_studio`, `ai_chat`). Non-chat commands are routed to the appropriate service. |
| **Voice input** | Uses `speech_recognition` with Google Speech API. Click the mic button, speak, text auto-fills into the input box. |
| **Markdown rendering** | AI responses with bold, code blocks, and lists are rendered visually in the chat bubble. |
| **History panel** | Right sidebar lists all past sessions with timestamps. Click any session to resume it. |

**Implementation:** Messages are saved to the DB before the API call. The API call runs in a background thread. When a response arrives, `AI_RESPONSE_RECEIVED` event fires and the UI thread renders the bubble.

---

### 4.3 AI Planner

**Files:** `ui/views/planner_view.py`, `services/ai_scheduling_service.py`, `services/task_service.py`

**What it does:** An AI-powered goal and project planning system that converts natural language goals into structured roadmaps with phases, milestones, and subtasks.

#### Sub-features:

| Feature | How it works |
|---|---|
| **AI Roadmap Generation** | User types a goal (e.g., "Learn React in 3 months"). The AI generates a multi-phase roadmap with weekly milestones. |
| **Phase & Task breakdown** | Each roadmap has phases → milestones → individual tasks. All stored in SQLite. |
| **Task status tracking** | Tasks can be marked as To Do / In Progress / Done. Progress bars update automatically. |
| **Smart scheduling** | AI suggests a realistic time schedule based on the goal's complexity and available days. |
| **Roadmap history** | All past roadmaps saved and accessible from the left sidebar. |

**Implementation:** Roadmap generation uses a structured JSON prompt to the LLM. The response is parsed and each task is written to the `tasks` table in SQLite. The UI subscribes to `ROADMAP_CREATED` event to refresh the view.

---

### 4.4 Summarizer (Knowledge Base)

**Files:** `ui/views/*` (summarizer section), `services/knowledge_pipeline.py`, `services/knowledge_service.py`, `services/knowledge_parser.py`, `services/embeddings/`

**What it does:** Ingests documents, PDFs, YouTube videos, and URLs, extracts their content, generates AI summaries, and stores them in a searchable knowledge base with semantic search.

#### Sub-features:

| Feature | How it works |
|---|---|
| **File ingestion** | Supports `.pdf`, `.txt`, `.docx`. Uses `pypdf` / `pdfplumber` / `python-docx` to extract raw text. |
| **YouTube ingestion** | Accepts YouTube URLs, downloads transcript via `pytube`, feeds transcript to the AI for summarization. |
| **URL / Website ingestion** | Fetches webpage HTML, strips tags, extracts clean readable text, then summarizes. |
| **AI Summarization** | Extracted text is chunked and sent to the LLM with a summarization prompt. Output is a structured summary with key points. |
| **Semantic Embeddings** | Each ingested document is embedded using `sentence-transformers` (local model, no cloud). Embeddings stored in SQLite. |
| **Semantic Search** | User queries are embedded in real-time and compared against stored document embeddings using cosine similarity. Returns the most relevant knowledge items. |
| **History with re-open** | All past summaries listed in history. Click any entry to re-open its full summary in the viewer. |

**Implementation:** Processing runs entirely in a background thread via `KnowledgePipeline`. The pipeline stages are: `VALIDATION → EXTRACTION → CHUNKING → EMBEDDING → SUMMARIZATION → STORAGE`. Events fired at each stage update a progress indicator in the UI.

**Why local embeddings?** Running `sentence-transformers` locally means semantic search works with zero additional API calls and zero cost, even on large knowledge bases.

---

### 4.5 Image Studio

**Files:** `ui/views/image_studio_view.py`, `services/image_service.py`, `ui/components/image_canvas.py`

**What it does:** A complete AI image generation studio. Users type a prompt, select a style and aspect ratio, and the AI generates a detailed image.

#### Sub-features:

| Feature | How it works |
|---|---|
| **Text-to-Image** | User prompt → AI prompt expansion (LLaMA) → NVIDIA `flux.2-klein-4b` → PNG saved locally |
| **AI Prompt Expansion** | Before generation, LLaMA rewrites the user's short idea into a 2-3 sentence detailed prompt describing lighting, composition, and subject. |
| **Style Presets** | 6 styles: None, Realistic, Anime, 3D Render, Cyberpunk, Sketch. Each adds powerful style modifier keywords to the prompt. |
| **Aspect Ratio** | 5 ratios: 1:1, 16:9, 9:16, 4:3, 3:4. The aspect ratio is encoded both in the API size parameter and in the prompt composition instruction. |
| **Reference Image Input** | Images can be dragged & dropped directly onto the prompt box or added via the 📎 button. Reference images are analyzed via vision API to extract a description that guides generation. |
| **Auto-Sanitizer** | If NVIDIA's content filter blocks a prompt, a word-swap table instantly replaces blocked terms (military → fantasy, soldiers → game champions, BGMI → squad arena game) and retries without any extra API call. |
| **Generation Timer** | After each image, the UI shows "Done ⏱ Xs" — exactly how many seconds it took. |
| **History panel** | All generated images stored in SQLite + local file system. Thumbnails shown in the right panel. Each can be re-loaded, downloaded, or deleted. |
| **Clear All History** | Deletes all image records from DB and removes the image files from disk. |
| **Save / Download** | "Save As" bar at the bottom — enter a filename and download the image as PNG, JPG, or WebP. |

**Image Generation Pipeline:**
```
User Prompt
  → AI Prompt Expansion (LLaMA, ~1s)
  → Style + Quality modifiers appended
  → NVIDIA flux.2-klein-4b API call (~2-3s)
  → Content filter check
      → If blocked: word-swap sanitize → retry
  → Decode base64 → Save to Aurex_Data/images/YEAR/
  → Update SQLite DB
  → Fire IMAGE_GEN_SUCCESS event
  → Canvas renders the image
  → Timer displayed
```

**Model Choice — `flux.2-klein-4b`:**
- Fastest NVIDIA NIM image model (2-3 seconds)
- Less restrictive content filtering vs `flux.1-dev` or `flux.1-schnell`
- 271K+ downloads on NVIDIA model hub
- Same API key, no additional cost

---

### 4.6 File Converter

**Files:** `ui/views/*` (converter section), `file_converter/`

**What it does:** Converts files between common formats without uploading to any cloud service.

#### Supported Conversions:
- PDF → DOCX
- PDF → TXT
- DOCX → PDF
- TXT → PDF
- Image format conversion (PNG ↔ JPG ↔ WebP)

**Implementation:** Uses `python-docx`, `reportlab`, `pdfplumber` and Pillow for format transformations. All processing is local.

**Why:** Avoids the need to use online tools that upload your private documents to external servers.

---

### 4.7 History

**Files:** `ui/views/` (history sections per feature), `services/history_service.py`

**What it does:** Every feature in FLOWSPACE automatically stores its output (chat messages, generated images, summaries, tasks) to SQLite. The History view provides a unified timeline of past activity.

- Filter by feature type
- Re-open any past result
- Delete individual items or clear all

---

### 4.8 Accounts

**File:** `ui/views/accounts_view.py`, `services/auth_service.py`

**What it does:** Local user account management. Users can register and log in. All data in the app is scoped to the logged-in user ID, so multiple users can share one FLOWSPACE installation with their own private data.

**Implementation:** Passwords are hashed before storage. Session token stored in `.aurex_session.json` for auto-login on next startup.

---

### 4.9 Settings

**File:** `ui/settings.py`

**What it does:** Allows the user to configure:
- API key (written to `.env`)
- Theme preferences
- Default generation quality
- App behavior toggles

---

## 5. API & Provider System

All LLM features use a single `aurex_api` client from `api_service.py`. This is an `openai.OpenAI` instance pointed at whichever provider's base URL was detected.

**Image generation** is separate — it hits NVIDIA's NIM image API directly via `requests`, since the OpenAI Python SDK's `images.generate()` endpoint is not compatible with NVIDIA's image models.

**Prompt flow for image generation:**
1. User text → LLaMA (via `aurex_api`) → expanded prompt
2. Expanded prompt → NVIDIA NIM `flux.2-klein-4b` (via raw HTTP) → base64 image

**Content filtering strategy:**
- A word-swap dictionary instantly replaces ~25 known blocked terms before retrying
- No secondary LLM call needed → saves 2-3 seconds per blocked prompt

---

## 6. Database Schema

All tables stored in a single local SQLite file (`Aurex_Data/flowspace.db`).

| Table | Stores |
|---|---|
| `users` | User accounts (id, username, password hash) |
| `chat_sessions` | AI chat sessions (id, title, created_at) |
| `chat_messages` | Individual messages per session (role, content, timestamp) |
| `tasks` | Planner tasks (title, status, due_date, roadmap_id) |
| `roadmaps` | AI-generated roadmaps (title, goal, phases JSON) |
| `knowledge_sources` | Ingested documents/URLs (title, type, summary) |
| `knowledge_chunks` | Text chunks with embeddings for semantic search |
| `image_history` | Generated images (prompt, style, aspect_ratio, local_path, gen_time) |

---

## 7. Known Limitations & Notes

| Item | Detail |
|---|---|
| **NVIDIA content filter** | The `flux.2-klein-4b` model has content restrictions. Military, weapons, and copyrighted game names may be blocked. The word-swap sanitizer handles most cases automatically. |
| **Image generation speed** | 2-5 seconds with `flux.2-klein-4b`. Generation time shown after each image in the UI. |
| **Embeddings model** | `sentence-transformers` loads on first startup, taking ~2-3 seconds. It only loads once per session. |
| **Voice input** | Requires an active internet connection for Google Speech-to-Text. |
| **API key required** | The app will not start without a valid API key in `.env`. |
| **Local storage** | All data (images, DB, session) stored in `Aurex_Data/` inside the project directory. |

---

*Documentation generated: June 2026 | Project: FLOWSPACE Cosmic Glass Workspace*
