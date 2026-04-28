# AI Task Planner + Debugger Agent

An agentic AI system powered by Claude that helps you plan multi-step tasks, explain concepts, debug code, and track your progress — all through a conversational interface.

---

## What It Does

| Mode | Description |
|------|-------------|
| **Plan** | Give it a goal, get a structured step-by-step task list |
| **Explain** | Ask it to explain any step, concept, or decision in plain English |
| **Debug** | Paste code or an error message, get a classified diagnosis and fix |
| **Classify** | Categorize a problem (e.g. logic error vs. config issue vs. dependency issue) |
| **Track** | Mark steps complete, view progress, resume where you left off |

---

## System Architecture

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
│  - Maintains conversation history                       │
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
│  - Sends structured prompts to Claude (claude-sonnet)   │
│  - Uses tool use / function calling for structured      │
│    outputs (task lists, error classifications)          │
│  - Manages token context and conversation memory        │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   Task Store (JSON)                      │
│                                                         │
│  tasks.json                                             │
│  {                                                      │
│    "goal": "Build a REST API for user auth",            │
│    "steps": [                                           │
│      { "id": 1, "title": "...", "done": false },        │
│      { "id": 2, "title": "...", "done": true  }         │
│    ],                                                   │
│    "history": [ ...conversation turns... ]              │
│  }                                                      │
└─────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Agent Orchestrator (`agent.py`)
The brain. Accepts user input, detects intent using a lightweight classifier prompt, and routes to the right handler. Keeps a rolling conversation history to maintain context across turns.

### 2. Planner Handler (`handlers/planner.py`)
Sends the user's goal to Claude with a system prompt that instructs it to return a structured JSON list of steps. Each step has an `id`, `title`, `description`, and `estimated_time`. Writes the result to `tasks.json`.

### 3. Explain Handler (`handlers/explainer.py`)
Takes a step ID or free-text question, fetches context from `tasks.json`, and asks Claude to explain it in plain English. Useful mid-task when something is unclear.

### 4. Debugger Handler (`handlers/debugger.py`)
Accepts a code snippet or error message. Asks Claude to:
1. **Classify** the error type (syntax / logic / runtime / dependency / config)
2. **Diagnose** the root cause
3. **Suggest** a fix with a corrected code block

### 5. Tracker Handler (`handlers/tracker.py`)
Reads and writes `tasks.json`. Lets you mark steps done, view a progress summary, and see what's next. No Claude call needed — pure local state management.

### 6. Claude API Layer (`claude_client.py`)
A thin wrapper around the Anthropic Python SDK. Handles:
- Sending messages with system prompts
- Parsing tool use / structured outputs
- Prompt caching for long conversations (reduces cost)

### 7. Task Store (`tasks.json`)
A local JSON file that persists your current goal, all steps, completion status, and conversation history. Acts as the system's memory between sessions.

---

## Data Flow Example

**User types:** `"Plan: build a REST API for user auth"`

```
1. Orchestrator detects intent → "plan"
2. Planner Handler builds prompt:
     system: "You are a task planner. Return a JSON array of steps..."
     user:   "Goal: build a REST API for user auth"
3. Claude returns structured JSON with 6-8 steps
4. Tracker Handler saves steps to tasks.json
5. CLI renders a numbered checklist to the user
```

**User types:** `"Debug: TypeError: cannot read property 'id' of undefined"`

```
1. Orchestrator detects intent → "debug"
2. Debugger Handler sends error + code context to Claude
3. Claude returns: { type: "runtime", cause: "...", fix: "..." }
4. CLI renders the diagnosis and suggested fix
```

---

## Project File Structure

```
ai-project/
├── README.md
├── requirements.txt
├── .env                    # ANTHROPIC_API_KEY lives here
├── main.py                 # Entry point, starts the CLI loop
├── agent.py                # Orchestrator — intent detection + routing
├── claude_client.py        # Anthropic SDK wrapper
├── tasks.json              # Persistent task + conversation store
└── handlers/
    ├── __init__.py
    ├── planner.py
    ├── explainer.py
    ├── debugger.py
    └── tracker.py
```

---

## Key Technical Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| AI Model | `claude-sonnet-4-6` | Best balance of speed, cost, and capability |
| Output format | Claude tool use (JSON) | Structured outputs for steps/classifications are more reliable than parsing prose |
| Persistence | Local JSON file | Simple, zero-dependency, easy to inspect and reset |
| UI | Python Rich (CLI) | Fast to build, looks good in terminal, no frontend needed |
| Prompt caching | Enabled on system prompts | Long system prompts are reused across turns — cuts cost significantly |

---

## How to Start Building (Step by Step)

### Step 1 — Set up your environment
```bash
mkdir ai-project && cd ai-project
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install anthropic rich python-dotenv
```

### Step 2 — Add your API key
Create a `.env` file:
```
ANTHROPIC_API_KEY=your_key_here
```
Get your key at [console.anthropic.com](https://console.anthropic.com)

### Step 3 — Build `claude_client.py` first
This is your foundation. A simple class that wraps `anthropic.Anthropic()`, sends messages, and returns responses. Test it with a hello-world prompt before building anything else.

### Step 4 — Build the Tracker Handler
No Claude needed — just read/write `tasks.json`. This forces you to define your data model early so every other handler knows what it's working with.

### Step 5 — Build the Planner Handler
One Claude call that returns a JSON list of steps and saves them via the Tracker. This is your first real end-to-end flow.

### Step 6 — Build the Debugger Handler
One Claude call with a well-crafted system prompt. Start with error classification, then add the fix suggestion.

### Step 7 — Build the Orchestrator + CLI loop
Wire all handlers together behind a single input loop. Add intent detection (a simple Claude call that returns `"plan"`, `"debug"`, `"explain"`, or `"track"`).

### Step 8 — Polish
Add the Explain Handler, conversation history, and prompt caching.

---

## Future Extensions

- **Web UI** — swap the CLI for a FastAPI backend + React frontend
- **File input** — paste a file path and it reads the code automatically
- **GitHub integration** — pull an issue or PR and plan the fix
- **Multi-session** — name and save multiple task plans
- **Voice input** — add Whisper for speech-to-text
