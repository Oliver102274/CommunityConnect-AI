# CommunityConnect AI

An AI-powered web application that helps people find local community assistance programs based on their needs and location.

> **Status:** MVP running end to end. Flask serves the frontend and `POST /api/chat` on <http://127.0.0.1:5050>, retrieves verified Miami-Dade resources with **Snowflake Cortex Search**, and writes grounded replies with **Snowflake Cortex AI** (`AI_COMPLETE`). The resource database currently holds a small, verified starter set.

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
│   ├── app.py              # Flask app: serves frontend + POST /api/chat (port 5050)
│   ├── requirements.txt    # Python dependencies
│   ├── test_connection.py  # Quick Snowflake connection check
│   └── services/
│       ├── __init__.py
│       └── snowflake_service.py  # Cortex Search retrieval + Cortex AI_COMPLETE
│
├── sql/
│   └── setup_resources.sql # Creates RESOURCES table, verified data, Cortex Search service
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

Copy the template. `.env` is ignored by Git and must never be committed.

```powershell
Copy-Item .env.example .env
```

Then choose **one** authentication option in `.env`:

- **Recommended — named connection:** set `SNOWFLAKE_CONNECTION_NAME` to a connection in `~/.snowflake/connections.toml` (the same file the Snowflake CLI / Cortex Code uses). No credentials are stored in the project. OAuth/browser connections may open a browser sign-in the first time.
- **Password:** set `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, and `SNOWFLAKE_PASSWORD` (only if your account allows password login).

Also set `SNOWFLAKE_WAREHOUSE` (e.g. `COMPUTE_WH`) if your connection has no default warehouse. Unedited `your_..._here` placeholders are ignored. Credentials are used only by the backend — never in the frontend.

### 3. Create the Snowflake data (one time)

Run `sql/setup_resources.sql` in Snowflake (Snowsight worksheet or `snow sql -f sql/setup_resources.sql`). It creates `COMMUNITYCONNECT_DB.PUBLIC.RESOURCES`, loads verified Miami-Dade resources (each with its official `SOURCE_URL`), and creates the Cortex Search service `RESOURCE_SEARCH`.

### 4. Install backend dependencies

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> If PowerShell blocks the activation script, run:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### 5. Start the app (frontend + API on one address)

```powershell
cd backend
python app.py
```

Then open the demo URL:

**<http://127.0.0.1:5050/?mode=live>**

Health check: <http://127.0.0.1:5050/api/health> should return:

```json
{ "service": "CommunityConnect AI backend", "status": "ok" }
```

### 6. (Optional) Frontend only, without the backend

Open <http://127.0.0.1:5050/?mode=demo>, or serve the static files:

```powershell
cd frontend
python -m http.server 8000
```

Then visit <http://localhost:8000/?mode=demo>. (Live mode from port 8000 calls Flask at `http://127.0.0.1:5050`, which would require CORS — use port 5050 instead.)

## How It Works (Live Mode)

1. The browser sends `POST /api/chat` to Flask (same origin, no CORS).
2. Flask opens **one** Snowflake connection for the request.
3. **Cortex Search** (`RESOURCE_SEARCH`) retrieves up to 6 relevant resources, filtered to `SERVICE_AREA = 'Miami-Dade County'` and, if a category is selected, to that category (primary or secondary). Combined requests such as "I'm a veteran who needs a job and food" return resources across all matching needs.
4. **Cortex AI** (`AI_COMPLETE`, model `llama3.3-70b`) writes a short reply using only the retrieved records. The prompt forbids inventing organizations or writing contact details; phone numbers and websites shown on cards come straight from the database.
5. The connection is closed and Flask returns `{ reply, resources, source }`.

Fallbacks (no fictional data, ever):

- Cortex Search unavailable → parameterized SQL retrieval (`source.retrieval = "sql_fallback"`).
- Cortex AI fails → a generic reply plus the real resource cards (`source.generation = null`).
- Snowflake unreachable → HTTP 503; the frontend shows an error message.

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
| **Live** (default) | Sends requests to the Flask backend at `POST /api/chat` and shows real Snowflake data. |
| **Demo** | No network calls. Returns example replies and **fictional placeholder** resource cards so the UI can be shown without the backend. Demo replies and cards are clearly labeled as examples, not verified recommendations. |

Demo resources are intentionally fictional (e.g. "Example Community Food Pantry") and contain **no real organizations, phone numbers, addresses, or websites**.

### Switching modes

- **Per page load:** add a URL parameter
  - `http://127.0.0.1:5050/?mode=live`
  - `http://127.0.0.1:5050/?mode=demo`
- **Change the default:** edit `DEFAULT_MODE` at the top of `frontend/js/api.js`:

  ```js
  const DEFAULT_MODE = "live"; // or "demo"
  ```

In live mode, if Flask isn't running, the chat shows a friendly "couldn't reach the assistant" message. Live mode **never** falls back to demo results.

### Which API URL the frontend uses

`frontend/js/api.js` picks the API base automatically:

| How the page is opened | API URL used |
| --- | --- |
| `file://` (double-clicked `index.html`) | `http://127.0.0.1:5050/api/chat` |
| Static dev server on port `8000` or `5500` (Live Server) | `http://127.0.0.1:5050/api/chat` |
| Served by Flask on port 5050 (recommended) | `/api/chat` (same-origin, relative) |

### Live mode error handling

| Situation | What the user sees |
| --- | --- |
| Flask not running / CORS blocked | "We couldn't reach the CommunityConnect assistant right now…" |
| No response within 30 seconds | "Sorry, that took too long…" |
| HTTP 5xx | "The assistant ran into a problem on our side…" |
| HTTP 4xx | "We couldn't process that request…" |
| Invalid JSON or wrong shape | "We received an unexpected response…" |

Responses are validated in `api.js`: `resources` must be an array (missing is treated as empty), entries without a name or description are skipped, and at most 20 cards are shown. All text is rendered as plain text, and only `http(s)` website links are allowed.

## Chat API Contract

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
  ],
  "source": { "retrieval": "cortex_search", "generation": "llama3.3-70b" }
}
```

`phone` and `website` may be `null`; the frontend shows "Not available" in that case. `source` is informational (shows whether Cortex Search / Cortex AI produced the answer); the frontend ignores it.

Errors return JSON `{ "error": "..." }` with HTTP `400` (invalid input: missing message, message over 1000 characters, unknown category, non-string location) or `503` (Snowflake unavailable).

### Testing live mode

1. Start Flask: `cd backend` then `python app.py`.
2. Open <http://127.0.0.1:5050/?mode=live> and send a message for each category, plus a combined one ("I'm a veteran who needs a job and food assistance in Miami.").
3. Or test the API directly (PowerShell):

   ```powershell
   Invoke-RestMethod http://127.0.0.1:5050/api/chat -Method Post -ContentType application/json `
     -Body '{"message":"I need food assistance in Miami","category":"food","location":"Miami-Dade County"}'
   ```

   `source.retrieval` should be `cortex_search` and `source.generation` should be `llama3.3-70b`.

### Integration status

- [x] `POST /api/chat` implemented with the agreed request/response format
- [x] Flask serves the frontend on port 5050 (same origin, no CORS needed)
- [x] Snowflake `RESOURCES` table with verified Miami-Dade records
- [x] Cortex Search retrieval, with SQL fallback
- [x] Cortex AI grounded replies
- [x] Tested end to end for veterans, food, employment, and combined requests
- [ ] Expand the resource database with more verified organizations

## Roadmap

- [x] **Stage 1:** Project structure, minimal Flask server, starter frontend
- [x] **Stage 2:** Chatbot UI, resource card components, and demo mode
- [x] **Stage 3:** Frontend prepared for live API integration
- [x] **Backend:** Flask `POST /api/chat`, Snowflake database with verified Miami-Dade resources
- [x] **Stage 4:** Cortex Search service for retrieval (RAG)
- [x] **Stage 5:** Cortex AI (`AI_COMPLETE`) grounded chat responses
- [x] **Stage 6:** Frontend/backend integration on one origin (port 5050)
- [ ] **Stage 7:** More verified resources, polish, and demo preparation
- [ ] **Future:** Expand to more counties and assistance categories
