# Transmute Engine

[![GitHub stars](https://img.shields.io/github/stars/HemantJaiman/TransmuteEngine?style=social)](https://github.com/HemantJaiman/TransmuteEngine)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

**An open-source, multi-agent enterprise codebase migration framework.**

Transmute Engine autonomously refactors and migrates legacy codebases (e.g., legacy Java/Vue) into modern stacks using distributed AI workflows. Built for enterprise scale, it moves beyond simple LLM wrappers by utilizing AST parsing, message queuing, and deterministic state machines.

---

## 🏗️ System Architecture

To handle repositories with thousands of files, Transmute Engine is decoupled into three highly fault-tolerant layers:

### 1. Ingestion & Dependency Mapping (Tree-sitter)
Traditional AI coding tools read code as plain text, missing crucial context. Transmute Engine uses **Tree-sitter** to parse the legacy codebase into an Abstract Syntax Tree (AST). 
* It mathematically maps the codebase, generating a Directed Acyclic Graph (DAG) of dependencies.
* **Why?** If `UserService.java` depends on `DatabaseConnection.java`, the system knows it *must* migrate the database file first.

### 2. The Asynchronous Spine (FastAPI + Redis)
Migrating an enterprise codebase synchronously hits API rate limits and memory constraints immediately.
* The **FastAPI** orchestrator receives the upload and the DAG.
* It breaks the migration down into hundreds of micro-tasks and pushes them into a **Redis** message queue.
* **Scale:** Multiple background worker nodes can pull from Redis simultaneously, migrating the codebase in parallel.

### 3. The Swarm State Machine (LangGraph + PydanticAI)
When a worker pulls a task from Redis, it triggers a deterministic AI workflow using **LangGraph**:
1. **Context Agent:** Gathers the legacy file and all its previously migrated dependencies.
2. **Translation Agent:** Converts the logic to the target stack using local (Llama 3 via Ollama) or hosted (GPT-4o/Gemini) models.
3. **Validation Agent (The Critic):** Uses **PydanticAI** for strict, type-safe validation of the output. It compiles and lints the code. 
4. **Self-Correction Loop:** If validation fails, LangGraph routes the error back to the Translation Agent to fix autonomously before marking the task complete.

## 🤝 Contributing
Because the system is modular, you can contribute to individual components without understanding the entire stack. Want to add a new legacy language parser? Focus on the `ingestion` module. Want to improve the LLM prompts? Focus on the `core_agents` module.
