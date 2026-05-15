# 🧬 Transmute Engine

[![GitHub stars](https://img.shields.io/github/stars/HemantJaiman/TransmuteEngine?style=social)](https://github.com/HemantJaiman/TransmuteEngine)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)


**A deterministic, self-healing AI Swarm for migrating enterprise codebases.**

Most AI coding assistants fail on large-scale migrations. They read code as flat text, lose architectural context, and crash when the LLM inevitably outputs a syntax error. 

**Transmute Engine** solves this by wrapping probabilistic AI models (Gemini, GPT-4, Llama 3) inside a strict, fault-tolerant distributed system. It parses Abstract Syntax Trees (AST), calculates mathematical dependencies, queues tasks via a message broker, and uses a LangGraph state machine to translate, validate, and compile code dynamically.

---

## 🏗️ System Architecture

To handle enterprise-scale repositories, Transmute is decoupled into four highly fault-tolerant layers:

### 1. Deep Ingestion (AST & Graph Theory)
You can't migrate `api.py` if the AI doesn't know what `database.py` does. 
* **Tree-sitter:** Parses legacy code into an AST to extract exact module dependencies instead of guessing based on text search.
* **Kahn’s Algorithm:** Executes a Topological Sort to calculate the mathematically perfect execution order. Standalone files are processed first; files that depend on them are processed later.
* **Tarjan’s Algorithm:** Actively hunts for Strongly Connected Components (SCCs). If it detects a circular dependency (e.g., File A imports File B, and File B imports File A), it bundles them into a single task so the AI has the exact context needed to merge and break the cycle.

### 2. The Distributed Spine (Redis & FastAPI)
Migrating a codebase synchronously blocks the main thread and hits API rate limits immediately.
* **FastAPI Orchestrator:** Acts as the traffic controller, handling UI requests and mapping the initial graph.
* **Redis Task Queue (`migration_tasks`):** Tasks are pushed to a persistent queue, allowing horizontal scaling. Multiple AI worker nodes can run on separate machines and pull tasks concurrently.
* **Redis Pub/Sub (`swarm_logs`):** Workers broadcast granular, real-time status updates ("Analyzing AST", "Compiling...") back to the Orchestrator.

### 3. The Swarm State Machine (LangGraph)
Workers don't just make an API call; they invoke a deterministic State Machine. All agents read and write to a shared `MigrationState`.
* **Context Agent:** Reads the source files from disk and formats the legacy code for the AI.
* **Translation Agent:** Uses Pydantic schemas to force the LLM to return strictly typed, pure code without conversational filler.
* **Validation Agent (The Critic):** Compiles the LLM's output using Python's native `ast.parse()`. 
* **Self-Healing Loop:** If the code is broken, the Validator blocks the disk write, captures the exact Python `SyntaxError`, and routes the state backward to the Translator to fix its own mistake (up to 3 retries).

### 4. The Model Factory
An abstraction layer that completely decouples the Swarm from specific AI providers. This prevents vendor lock-in and allows the system to switch "brains" instantly. Currently supports:
* **Google Gemini** (Optimized for Gemini 2.5 Flash)
* **OpenAI** (GPT-4o)
* **Ollama** (Local, free, rate-limitless execution via Llama 3)

---

## 🔀 Data Flow: How It Works

1. **Upload:** User selects a legacy directory and target stack via the Web UI.
2. **Map:** FastAPI builds the AST DAG, resolves circular dependencies via Tarjan's, and pushes a sorted task list to Redis.
3. **Process:** Background Python workers pull tasks. The LangGraph agents context-gather, translate, and self-correct syntax errors.
4. **Telemetry:** As workers process files, they push logs to Redis Pub/Sub. FastAPI streams these via **WebSockets** to the UI's live terminal.
5. **Finalize:** Once the queue hits zero, the AI generates a `MIGRATION_GUIDE.md` and packages the new codebase into a downloadable `.zip`.

---

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* Redis (Running locally or via Docker)
* API Keys (Google AI Studio or OpenAI)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/HemantJaiman/TransmuteEngine.git
   cd TransmuteEngine
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment:**
   Create a `.env` file in the root directory:
   ```bash
   GEMINI_API_KEY=your_google_ai_key_here
   OPENAI_API_KEY=your_openai_key_here  # Optional
   REDIS_HOST=localhost
   REDIS_PORT=6379
   ```

4. **Start the Redis Broker:**
   ```bash
   docker run -d -p 6379:6379 redis
   ```

## 🕹️ Usage

Transmute requires two terminals to run its decoupled architecture.

### Terminal 1: Start the Orchestrator & UI

```bash
uvicorn src.api.main:app --reload
```

### Terminal 2: Boot an AI Worker Node

```bash
python src/queues/worker.py
```

### Run a Migration:

1. Open your browser to **http://localhost:8000**.
2. Upload your legacy codebase folder.
3. Select your Target Architecture (e.g., FastAPI + Vue 3) and your preferred AI Engine.
4. Click **Initialize Swarm** and watch the live telemetry stream via WebSockets.
5. Once complete, click **Generate Setup Guide**, then download your fully modernized `.zip` codebase.

## 🤝 Contributing

Migrations are mathematically complex. If you have optimizations for the AST parser, Tree-sitter implementations for new legacy languages (e.g., C#, Ruby), or improvements for the LangGraph loop efficiency, open a PR. Focus on individual modules (ingestion, core_agents, or queues) without needing to understand the entire stack.  