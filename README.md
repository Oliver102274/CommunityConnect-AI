# CommunityConnect AI

An AI-powered web application that helps people find local community assistance programs based on their needs and location.

> **Status:** Stage 3 — frontend is ready for live integration and works in **demo mode** today. The Flask `POST /api/chat` endpoint, Snowflake Cortex AI, Cortex Search (RAG), and resource database are **not implemented yet** (owned by Developer 2).

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
│   │   ├── api.js          # API layer: demo/live mode, POST /api/chat
│   │   └── main.js         # UI logic: chat, categories, resource cards
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

## Frontend Features (Stage 2)

- Responsive header with mobile menu, "Powered by Snowflake" label, and a Demo/Live mode badge
- Welcome section with a call to action
- Three selectable assistance categories (Veteran Support, Food Assistance, Employment) that pre-fill a starter message
- Chatbot interface: welcome message, user/AI message styles, Enter to send (Shift+Enter for a new line), typing indicator, auto-scroll, disabled send button while empty or loading, friendly error messages, and clickable example prompts
- Reusable resource cards (name, category, description, location, phone, website) with "Not available" fallbacks for missing details
- Safe rendering: backend text is inserted as plain text and only `http(s)` links are allowed
- Accessible markup (skip link, ARIA live regions, keyboard focus styles) and reduced-motion support

## Demo Mode vs. Live Mode

| Mode | What it does |
| --- | --- |
| **Demo** (default) | No network calls. Returns example replies and **fictional placeholder** resource cards so the UI can be shown without the backend. Demo replies and cards are clearly labeled as examples, not verified recommendations. |
| **Live** | Sends requests to the Flask backend at `POST /api/chat`. |

Demo resources are intentionally fictional (e.g. "Example Community Food Pantry") and contain **no real organizations, phone numbers, addresses, or websites**.

### Switching modes

- **Per page load:** add a URL parameter
  - `http://localhost:8000/?mode=live`
  - `http://localhost:8000/?mode=demo`
- **Change the default:** edit `DEFAULT_MODE` at the top of `frontend/js/api.js`:

  ```js
  const DEFAULT_MODE = "demo"; // change to "live" once the backend is ready
  ```

In live mode, if Flask isn't running, the chat shows a friendly "couldn't reach the assistant" message. Live mode **never** falls back to demo results.

### Which API URL the frontend uses

`frontend/js/api.js` picks the API base automatically:

| How the page is opened | API URL used |
| --- | --- |
| `file://` (double-clicked `index.html`) | `http://127.0.0.1:5000/api/chat` |
| Static dev server on port `8000` or `5500` (Live Server) | `http://127.0.0.1:5000/api/chat` |
| Served by Flask (any other origin) | `/api/chat` (same-origin, relative) |

### Live mode error handling

| Situation | What the user sees |
| --- | --- |
| Flask not running / CORS blocked | "We couldn't reach the CommunityConnect assistant right now…" |
| No response within 30 seconds | "Sorry, that took too long…" |
| HTTP 5xx | "The assistant ran into a problem on our side…" |
| HTTP 4xx | "We couldn't process that request…" |
| Invalid JSON or wrong shape | "We received an unexpected response…" |

Responses are validated in `api.js`: `resources` must be an array (missing is treated as empty), entries without a name or description are skipped, and at most 20 cards are shown. All text is rendered as plain text, and only `http(s)` website links are allowed.

## Proposed Chat API Contract

> This contract is **proposed** and will be confirmed by Developer 2 before integration.

`POST /api/chat`

Request:

```json
{
  "message": "I need employment assistance",
  "category": "employment",
  "location": "Miami-Dade County"
}
```

Allowed `category` values: `"veterans"`, `"food"`, `"employment"`, or `null` (all categories).

Response:

```json
{
  "reply": "Here are some resources that may help.",
  "resources": [
    {
      "name": "Organization name",
      "category": "employment",
      "description": "Description",
      "location": "Miami-Dade County",
      "phone": null,
      "website": null
    }
  ]
}
```

`phone` and `website` may be `null`; the frontend shows "Not available" in that case.

### Connecting the backend (for Developer 2)

1. Add a `POST /api/chat` route in `backend/app.py` that accepts and returns the JSON above.
2. Choose how the frontend reaches Flask:
   - **Option A — separate servers (default):** the frontend on `localhost:8000` calls `http://127.0.0.1:5000`. Enable CORS in Flask (e.g. `flask-cors`) for that origin.
   - **Option B — Flask serves the frontend:** serve the `frontend/` folder from Flask on port 5000. The frontend then uses relative URLs automatically and CORS is not needed.
3. Test with `?mode=live`, then set `DEFAULT_MODE = "live"` in `frontend/js/api.js`.
4. Return only verified resource data from Snowflake — never generated contact details.

The endpoint URL is configured in `frontend/js/api.js` (`API_BASE` / `CHAT_ENDPOINT`).

### Testing live mode

1. Start Flask: `cd backend` then `python app.py` (port 5000).
2. Start the frontend: `cd frontend` then `python -m http.server 8000`.
3. Open <http://localhost:8000/?mode=live> and send a message for each category.
4. Check the browser DevTools **Network** tab: the request to `/api/chat` should return `200` with the JSON shape above.

### Integration status and remaining requirements

- [x] Frontend sends the agreed request and validates the agreed response
- [x] Error handling for network, timeout, HTTP, and invalid responses
- [x] Tested against a mock response matching the contract (not committed)
- [ ] Developer 2: implement `POST /api/chat` in Flask
- [ ] Developer 2: enable CORS for `http://localhost:8000` (or serve `frontend/` from Flask)
- [ ] Developer 2: return the agreed `reply` / `resources` format, using `veterans`, `food`, `employment` category values
- [ ] Both: test end to end with `?mode=live`, then switch `DEFAULT_MODE` to `"live"`

## Roadmap

- [x] **Stage 1:** Project structure, minimal Flask server, starter frontend
- [x] **Stage 2:** Chatbot UI, resource card components, and demo mode
- [x] **Stage 3:** Frontend prepared for live API integration (backend endpoint pending)
- [ ] **Backend (Developer 2):** Snowflake database with Miami-Dade resource data
- [ ] **Stage 4:** Cortex Search service for retrieval (RAG)
- [ ] **Stage 5:** Cortex AI REST API integration for chat responses
- [ ] **Stage 6:** Frontend/backend integration and API endpoints
- [ ] **Stage 7:** Testing, polish, and demo preparation
- [ ] **Future:** Expand to more counties and assistance categories
