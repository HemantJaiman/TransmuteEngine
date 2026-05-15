# Transmute Engine

[![GitHub stars](https://img.shields.io/github/stars/HemantJaiman/TransmuteEngine?style=social)](https://github.com/HemantJaiman/TransmuteEngine)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

**An open-source, multi-agent enterprise codebase migration framework.**

Transmute Engine autonomously refactors and migrates legacy codebases (e.g., legacy Java/Vue) into modern stacks using distributed AI workflows. Built for enterprise scale, it moves beyond simple LLM wrappers by utilizing AST parsing, message queuing, and deterministic state machines.

---

🧬 Transmute Engine
An enterprise-grade, deterministic AI Swarm for migrating legacy codebases.

Traditional AI coding assistants fail on large-scale migrations because they lack structural context and crash when the LLM hallucinates bad syntax. Transmute Engine solves this by wrapping probabilistic AI models (Gemini, GPT-4, Llama 3) in a deterministic, fault-tolerant distributed system.

Instead of blindly feeding files to an LLM, Transmute parses the Abstract Syntax Tree (AST), maps mathematical dependencies, queues tasks via a message broker, and uses a self-healing LangGraph state machine to translate, validate, and compile the code.

🏗️ System Architecture
Transmute is built on a decoupled, cloud-native microservices architecture, separated into four distinct layers:

1. The Orchestrator (FastAPI)
The centralized controller and API gateway. It serves the static frontend and exposes REST/WebSocket endpoints.

/api/v1/migrate: The ingestion trigger. It accepts user constraints, parses the codebase, maps the execution graph, and pushes tasks to Redis.

/ws/logs: A WebSocket connection that listens to Redis Pub/Sub to stream live telemetry from the Swarm directly to the frontend.

/api/v1/generate_guide & /api/v1/download: Post-migration endpoints that use the AI to compile a setup guide (MIGRATION_GUIDE.md) and package the result into a .zip archive.

2. The Distributed Spine (Redis)
We do not block the main thread. All migration tasks are handled asynchronously to allow for horizontal scaling of AI Worker nodes.

Task Queue (migration_tasks): The Orchestrator pushes finalized migration payloads here. Workers continuously poll this queue.

Pub/Sub Channel (swarm_logs): Workers publish granular, real-time status updates ("Analyzing AST", "Compiling...") to this channel, which the Orchestrator catches and pipes to the UI.

3. The AI Swarm (LangGraph State Machine)
Workers do not make simple API calls; they invoke a deterministic State Machine. All agents read and write to a shared MigrationState dictionary.

Context Agent: Reads the source file(s) from disk and loads the legacy code into memory.

Translator Agent: Uses strict Pydantic schemas to force the LLM to return purely compiled code (no conversational filler).

Validation Agent (The Critic): Compiles the LLM's output using Python's native ast.parse().

Self-Healing: If the code throws a SyntaxError, the Validator blocks the write operation, captures the exact traceback, and routes the state backward to the Translator for a retry (up to 3 attempts).

4. The Model Factory
An abstraction layer that decouples the Swarm from specific AI providers. This ensures the system never breaks if an API changes. It currently routes to:

Google Gemini (via google-genai SDK)

OpenAI GPT-4o

Local Llama 3 (via Ollama for free, rate-limitless execution)

🔀 Data Flow & Algorithms
Phase 1: Deep Ingestion
Tree-sitter AST: Parses the legacy codebase to extract raw import statements and map module dependencies accurately.

Tarjan’s Algorithm (SCC): Scans the graph for Strongly Connected Components. If a circular dependency is found (e.g., File A imports File B, and File B imports File A), they are grouped into a single "SCC Bundle" list.

Kahn’s Algorithm (Topological Sort): Calculates the mathematically perfect execution order. Standalone files are processed first; files that depend on them are processed later.

Phase 2: Execution & Self-Healing
A Worker pulls a file (or an SCC Bundle) from Redis.

If it encounters an SCC Bundle, the Context Agent merges the files together, and the Translator explicitly prompts the LLM to resolve the circular dependency into a single cohesive file.

The LLM translates the logic.

If rate limits (429) or syntax errors occur, the state machine gracefully catches them, logs them via Pub/Sub, and retries the specific node without crashing the worker.

🚀 Getting Started
Prerequisites
Python 3.10+

Redis (Running locally or via Docker)

API Keys (Google Gemini or OpenAI)

Installation
Clone the repository:

Bash
git clone https://github.com/yourusername/transmute-engine.git
cd transmute-engine
Install dependencies:

Bash
pip install -r requirements.txt
Configure Environment:
Create a .env file in the root directory:

Code snippet
GEMINI_API_KEY=your_google_ai_key_here
OPENAI_API_KEY=your_openai_key_here  # Optional
REDIS_HOST=localhost
REDIS_PORT=6379
Start the Redis Broker:

Bash
docker run -d -p 6379:6379 redis
🕹️ Usage
Transmute requires two terminals to run its decoupled architecture.

Terminal 1: Start the Orchestrator & UI

Bash
uvicorn src.api.main:app --reload
Terminal 2: Boot an AI Worker Node

Bash
python src/queues/worker.py
Run a Migration:

Open your browser to http://localhost:8000.

Upload your legacy codebase folder.

Select your Target Architecture (e.g., FastAPI + Vue 3) and your preferred AI Engine.

Click Initialize Swarm and watch the live telemetry stream via WebSockets.

Once complete, click Generate Setup Guide, then download your fully modernized .zip codebase.

🤝 Contributing
Migrations are mathematically complex. If you have optimizations for the AST parser or the LangGraph loop efficiency, PRs are welcome.
