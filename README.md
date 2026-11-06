# CommunityConnect AI

An AI-powered web application that helps people find local community assistance programs based on their needs and location.

> **Status:** Stage 1 — initial project structure. The Snowflake Cortex AI chatbot, Cortex Search (RAG), and resource database are **planned, not yet implemented**.

---

## The Problem

People in need of help — veterans, families facing food insecurity, and job seekers — often struggle to find the right local programs. Information is scattered across many websites, eligibility rules are confusing, and it is hard to know where to start.

## Our Solution

CommunityConnect AI provides a simple chat-based assistant. Users describe their situation in plain language, and the app returns relevant, local assistance programs as easy-to-read resource cards.

Our initial focus is **Miami-Dade County**, with three categories:

- Veteran support
- Food assistance
- Employment

## Technology Stack

| Layer | Technology |
| --- | --- |
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Flask |
| Database | Snowflake |
| AI | Snowflake Cortex AI REST API |
| RAG | Snowflake Cortex Search |
| Version control | Git and GitHub |

## MVP Features

- Chatbot interface where users describe their needs
- AI-generated answers grounded in a curated resource database (RAG)
- Resource cards with program name, description, contact info, and location
- Filtering by category: veterans, food, employment
- Miami-Dade County coverage

## Project Structure

```text
CommunityConnect-AI/
├── frontend/
│   ├── index.html          # Main page
│   ├── css/
│   │   └── styles.css      # Styles
│   ├── js/
│   │   └── main.js         # Frontend logic
│   └── assets/             # Images and icons
│
├── backend/
│   ├── app.py              # Flask application
│   ├── requirements.txt    # Python dependencies
│   └── services/           # Snowflake / Cortex integrations (future)
│       └── __init__.py
│
├── .env.example            # Environment variable template
├── .gitignore
└── README.md
```

## Developer Responsibilities

| Developer | Responsibilities |
| --- | --- |
| Developer 1 | Frontend, chatbot interface, resource cards, frontend/backend integration |
| Developer 2 | Flask backend, Snowflake database, Cortex AI, RAG, API endpoints |

## Local Setup (Windows + VS Code)

### Prerequisites

- [Python 3.10+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
- [VS Code](https://code.visualstudio.com/)

### 1. Clone the repository

```powershell
git clone https://github.com/Oliver102274/CommunityConnect-AI.git
cd CommunityConnect-AI
code .
```

### 2. Set up environment variables

Copy the template and fill in your own values. `.env` is ignored by Git and must never be committed.

```powershell
Copy-Item .env.example .env
```

Snowflake authentication settings will be finalized by Developer 2. Credentials are used only by the backend — never in the frontend.

### 3. Install backend dependencies

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> If PowerShell blocks the activation script, run:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### 4. Start the Flask server

```powershell
python app.py
```

Verify it works by opening <http://127.0.0.1:5000/api/health> in your browser. You should see:

```json
{ "service": "CommunityConnect AI backend", "status": "ok" }
```

### 5. Open the frontend

Open `frontend/index.html` directly in your browser, or serve it locally:

```powershell
cd frontend
python -m http.server 8000
```

Then visit <http://localhost:8000>. (The VS Code **Live Server** extension also works.)

## Roadmap

- [x] **Stage 1:** Project structure, minimal Flask server, starter frontend
- [ ] **Stage 2:** Chatbot UI and resource card components
- [ ] **Stage 3:** Snowflake database with Miami-Dade resource data
- [ ] **Stage 4:** Cortex Search service for retrieval (RAG)
- [ ] **Stage 5:** Cortex AI REST API integration for chat responses
- [ ] **Stage 6:** Frontend/backend integration and API endpoints
- [ ] **Stage 7:** Testing, polish, and demo preparation
- [ ] **Future:** Expand to more counties and assistance categories
