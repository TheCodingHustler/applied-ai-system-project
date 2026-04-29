#LINK TO THE DEMO VIDEO: https://www.youtube.com/watch?v=f2mK1cZQ6lc

# AI Task Planner + Debugger Agent

> A conversational AI system that helps developers plan projects, debug code, explain concepts, and track their progress — all from the terminal.

---

## Original Project (Modules 1–3)

The foundation of this project was an exploratory study into how large language models can act as intelligent assistants for software engineers. In Modules 1–3, three candidate systems were designed and evaluated: a Personal Research Assistant that summarized documents, a Document Q&A Bot using retrieval-augmented generation (RAG), and a Task Planner + Debugger Agent. The original goal was to identify which architecture could best combine planning, reasoning, and debugging into a single coherent workflow, rather than building a narrowly scoped tool. This project is the full implementation of that third idea — the one judged most useful, most teachable, and most representative of how modern AI agents are built in practice.

---

## Title and Summary

**AI Task Planner + Debugger Agent** is a terminal-based AI assistant powered by Claude (Anthropic). You give it a goal — like "build a REST API for user authentication" — and it breaks it down into a specific, ordered plan you can work through step by step. Along the way, you can ask it to explain any step, paste in broken code or error messages to get a structured diagnosis and fix, and mark steps as complete to track your progress. The system remembers your current plan between messages and uses that context to give answers that are relevant to exactly what you are building.

This matters because most developers waste significant time not on the actual coding, but on figuring out *what to do next*, *why something broke*, and *what a concept means in their specific context*. This system addresses all three problems in one interface.

---

## Architecture Overview

The system is built as a routed multi-handler agent. Every message the user sends passes through an **orchestrator** (`agent.py`) that makes one Claude API call to classify the intent, then dispatches to the right handler. Each handler is isolated: it has its own system prompt, its own Claude tool definition (where applicable), and its own responsibility. The handlers never call each other — they communicate only through the shared **task store** (`tasks.json`), which is a local JSON file that persists the current goal, all steps, and completion status.

```
┌─────────────────────────────────────────────────────────┐
│                      User Interface                      │
│              (CLI via Python Rich library)               │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                     Agent Orchestrator                   │
│                                                         │
│  - Reads user input                                     │
│  - Detects intent (plan / explain / debug / track)      │
│  - Routes to the correct handler                        │
│  - Maintains rolling conversation history (last 10 turns)│
└──────┬──────────┬──────────┬──────────┬────────────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
  │Planner │ │Explain │ │Debugger│ │Tracker │
  │Handler │ │Handler │ │Handler │ │Handler │
  └────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘
       │          │          │          │
       └──────────┴──────────┴──────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    Claude API Layer                      │
│                                                         │
│  - Sends structured prompts to claude-sonnet-4-6        │
│  - Uses tool use / function calling for structured      │
│    outputs (step lists, error classifications)          │
│  - Prompt caching on system prompts (reduces cost)      │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   Task Store (tasks.json)                │
│                                                         │
│  {                                                      │
│    "goal": "Build a REST API for user auth",            │
│    "steps": [                                           │
│      { "id": 1, "title": "...", "done": false },        │
│      { "id": 2, "title": "...", "done": true  }         │
│    ]                                                    │
│  }                                                      │
└─────────────────────────────────────────────────────────┘
```

### Component Breakdown

| File | Responsibility |
|------|---------------|
| `main.py` | CLI loop, Rich rendering of all output types |
| `agent.py` | Intent detection, routing, conversation history |
| `claude_client.py` | Anthropic SDK wrapper, prompt caching |
| `handlers/planner.py` | Claude tool-use → structured step list, saves to store |
| `handlers/debugger.py` | Claude tool-use → error type, root cause, fixed code |
| `handlers/explainer.py` | Free-text Q&A with current task context injected |
| `handlers/tracker.py` | Local read/write of `tasks.json`, no Claude calls |

---

## Setup Instructions

### Prerequisites
- Python 3.11 or higher
- An Anthropic API key — get one at [console.anthropic.com](https://console.anthropic.com)

### 1. Clone or download the project

```bash
cd "ai project"
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your API key

```bash
cp .env.example .env
```

Open `.env` and fill in your key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

### 5. Run the app

```bash
python main.py
```

You should see the welcome screen. Start typing a goal, a debug question, or anything you want explained.

---

## Sample Interactions

### Example 1 — Planning a project goal

**Input:**
```
Build a REST API for user authentication using Python and Flask
```

**Output (abbreviated):**
```
╭─ Plan Created ──────────────────────────────────────────────────────╮
│ Build a REST API for user authentication using Python and Flask     │
╰─────────────────────────────────────────────────────────────────────╯

 #  Step                              Description                           Est. Time
 1  Set up project structure          Create a virtual environment, init     30 min
                                      a Git repo, install flask,
                                      flask-jwt-extended, bcrypt, and
                                      python-dotenv
 2  Design the database schema        Define a User model with id,           1 hour
                                      email, password_hash, created_at.
                                      Use SQLAlchemy with SQLite for dev
 3  Implement user registration       POST /auth/register — validate         1–2 hours
                                      input, hash password with bcrypt,
                                      save user to db, return 201
 4  Implement login + JWT issuance    POST /auth/login — verify password,    1–2 hours
                                      issue access + refresh tokens
 ...
```

---

### Example 2 — Debugging a runtime error

**Input:**
```
TypeError: Cannot read properties of undefined (reading 'map')
  at UserList (UserList.jsx:12)
```

**Output:**
```
╭─ Classification ────────╮
│  RUNTIME ERROR          │
╰─────────────────────────╯

╭─ Root Cause ──────────────────────────────────────────────────────────────────╮
│ The `users` prop passed to UserList is undefined at the time the component    │
│ renders. React tries to call .map() on it before the data has loaded,         │
│ resulting in a TypeError. This usually happens when the parent component      │
│ hasn't initialized the state value before passing it down.                    │
╰───────────────────────────────────────────────────────────────────────────────╯

╭─ How to Fix ──────────────────────────────────────────────────────────────────╮
│ 1. Initialize the users state as an empty array, not undefined or null.       │
│ 2. Add a guard clause in UserList to handle the loading state.                │
╰───────────────────────────────────────────────────────────────────────────────╯

╭─ Fixed Code ──────────────────────────────────────────────────────────────────╮
│  1  // Parent component                                                       │
│  2  const [users, setUsers] = useState([]);  // was: useState(null)           │
│  3                                                                            │
│  4  // UserList.jsx                                                           │
│  5  function UserList({ users = [] }) {                                       │
│  6    if (!users.length) return <p>Loading...</p>;                            │
│  7    return users.map(u => <div key={u.id}>{u.name}</div>);                  │
│  8  }                                                                         │
╰───────────────────────────────────────────────────────────────────────────────╯
```

---

### Example 3 — Asking an explanation mid-task

**Input:**
```
What does step 3 mean? What exactly is JWT and why do I need it here?
```

**Output:**
```
╭─ Explanation ─────────────────────────────────────────────────────────────────╮
│ In step 3 of your Flask auth API plan, JWT (JSON Web Token) is the           │
│ mechanism you'll use to prove a user is logged in without storing session     │
│ state on the server.                                                          │
│                                                                               │
│ When a user logs in successfully, your server creates a JWT — a small         │
│ signed string that encodes the user's ID and an expiry time. The client       │
│ stores this token (usually in localStorage or a cookie) and sends it in the  │
│ Authorization header on every protected request. Your server verifies the     │
│ signature and reads the user ID without touching a database.                  │
│                                                                               │
│ You need it here because your API is stateless — there are no sessions.       │
│ flask-jwt-extended makes this easy: @jwt_required() on any route that         │
│ should only be accessible to logged-in users.                                 │
╰───────────────────────────────────────────────────────────────────────────────╯
```

---

### Example 4 — Tracking progress

**Input:**
```
done step 1
```

**Output:**
```
✓ Step 1 marked as completed.

  ✓  1  Set up project structure
  ○  2  Design the database schema
  ○  3  Implement user registration
  ○  4  Implement login + JWT issuance
  ...
```

---

## Design Decisions

| Decision | Choice | Trade-off |
|----------|--------|-----------|
| **Intent detection** | Separate Claude call using tool-use | Adds one API call per message, but is far more reliable than regex or keyword matching. Users phrase things unpredictably — a model handles that gracefully. |
| **Structured output** | Claude tool-use (function calling) with JSON schema | Forces Claude to return data in a shape the code can use, not prose that needs to be parsed. The schema also acts as a contract between the prompt and the code. |
| **Persistence** | Local `tasks.json` | A database (SQLite, Postgres) would be more scalable but adds setup friction. JSON is zero-dependency, human-readable, and easy to inspect or reset manually — the right choice for a single-user CLI tool. |
| **Prompt caching** | Enabled via `cache_control: ephemeral` on system prompts | System prompts are long and identical across turns. Caching them means only the new user message is billed at full price after the first call, which cuts costs significantly during a long planning session. |
| **Handler isolation** | Each handler owns its own system prompt and tools | Keeps prompts focused. A planner prompt optimized for structure would conflict with a debugger prompt optimized for diagnosis if they shared context. Isolation also makes each handler independently testable. |
| **Rich CLI over web UI** | Python `rich` library | A web frontend would require a backend server, CORS, and a build step — none of which add value to a terminal-native developer tool. Rich gives formatted tables, syntax highlighting, and panels in ~20 lines of code. |
| **Rolling conversation history** | Last 20 messages kept in memory | Keeps the model context-aware ("what does step 3 mean?" resolves correctly because the plan is in history) without risking context overflow on long sessions. History is in-memory only and resets on restart — intentional, since `tasks.json` already persists the goal and steps. |

---

## Testing Summary

### What worked well

- **Intent detection was accurate** across a wide range of natural phrasings. Saying "I want to build a login system", "plan: auth API", or simply "REST API with JWT" all correctly routed to the planner.
- **Tool-use produced consistent structured output.** The step lists came back with the correct fields every time, which made the rendering logic simple and reliable.
- **Context injection in the explainer worked as expected.** When a plan was active, asking "what does step 2 mean?" produced answers specific to the current goal, not generic explanations.
- **Tracker logic was robust.** Phrases like "done step 3", "finish step 3", and "I completed step 3" all parsed correctly via the regex patterns in `tracker.py`.

### What didn't work / limitations discovered

- **Very short or ambiguous inputs sometimes misclassified.** A message like "JWT" alone was sometimes classified as `explain` when the user intended to debug a JWT error. Adding more input context (pasting the actual error) resolved this.
- **The planner doesn't yet handle multi-session goals.** Starting a new plan overwrites the previous one with no warning. For a real tool, a named-session system or a confirmation prompt would be needed.
- **Conversation history is lost on restart.** The task steps persist across sessions (via `tasks.json`), but the conversational context does not. If you close the terminal and reopen it, the model no longer "remembers" what was discussed — only what is in the task file.
- **Fixed code snippets are not always language-aware.** The debugger asks Claude to identify the language, but if no code is pasted (just an error message), the language field is absent and the syntax highlighter defaults to plain text.

### What I learned

The biggest lesson was that **prompt engineering and data modeling are equally important**. The first version of the planner returned step descriptions that were vague and generic. Adding one constraint to the system prompt ("no vague steps — instead of 'set up project', write 'create a Python venv and install flask, sqlalchemy, pytest'") produced dramatically more useful output. The fix was in the prompt, not the code.

The second major lesson was that **structured output via tool-use is essential for agentic systems**. Early experiments used free-form text responses and tried to parse them. This broke constantly — the model would sometimes add commentary, vary its formatting, or include markdown the parser didn't expect. Switching to tool-use with a fixed schema eliminated the entire category of parsing bugs.

---

## Reflection

Building this system taught me that AI agents are fundamentally about **routing and context management**, not just prompting. The hardest problems were not "how do I get Claude to write a good step?" — that was straightforward with the right system prompt. The hard problems were: how does the system know what the user wants? How does it pass the right context to the model without overwhelming it? How does it store and retrieve state so that answers feel coherent across a long conversation?

The intent detection layer was the most important architectural decision. Without it, the system would need the user to explicitly type "plan:", "debug:", or "explain:" as a prefix — which is fine for a demo but breaks down immediately when real people use it. Letting a model classify intent means the interface is natural, and natural interfaces are the ones people actually use.

More broadly, this project changed how I think about AI as a problem-solving tool. The model is not the product — it is the reasoning engine inside a product. The product is the data model, the routing logic, the context that gets passed in, and the rendering that makes the output readable. Getting those right is a software engineering problem, not an AI problem. The AI part, once the surrounding system is solid, almost takes care of itself.

---

## Project File Structure

```
ai-project/
├── README.md
├── requirements.txt
├── .env                    ← ANTHROPIC_API_KEY (not committed)
├── .env.example            ← template for new contributors
├── main.py                 ← entry point, Rich CLI loop
├── agent.py                ← orchestrator: intent detection + routing
├── claude_client.py        ← Anthropic SDK wrapper with prompt caching
├── tasks.json              ← persistent task store (goal + steps)
└── handlers/
    ├── __init__.py
    ├── planner.py          ← structured step generation
    ├── explainer.py        ← context-aware Q&A
    ├── debugger.py         ← error classification + fix
    └── tracker.py          ← local state read/write
```

---

## Future Extensions

- **Web UI** — FastAPI backend + React frontend, same agent logic underneath
- **File input** — pass a file path and the system reads the code before debugging
- **GitHub integration** — pull an issue or PR URL and plan the fix automatically
- **Multi-session** — name and save multiple task plans, switch between them
- **Voice input** — Whisper transcription → same agent pipeline
