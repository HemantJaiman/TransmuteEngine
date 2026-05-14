from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

# Import our Phase 1 Graph and Phase 2 Broker
from ingestion.graph import DependencyGraph
from queues.broker import TaskBroker

app = FastAPI(title="Transmute Engine Orchestrator")
broker = TaskBroker()

class MigrationRequest(BaseModel):
    target_directory: str

@app.post("/api/v1/migrate")
async def start_migration(request: MigrationRequest):
    """
    1. Validates the directory.
    2. Builds the Dependency Graph (AST Parsing).
    3. Pushes the ordered tasks to Redis.
    """
    if not os.path.exists(request.target_directory):
        raise HTTPException(status_code=400, detail="Directory not found")

    try:
        # Step 1: Initialize our AST Engine
        engine = DependencyGraph(request.target_directory)
        engine.build_graph()
        
        # Step 2: Calculate the exact order of operations
        migration_order = engine.get_migration_order()
        
        # Step 3: Push tasks to the asynchronous queue
        tasks_queued = broker.push_migration_batch(migration_order)
        
        return {
            "status": "success",
            "message": "Codebase mapped and queued for AI Swarm.",
            "total_files_queued": tasks_queued,
            "execution_order": migration_order
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/status")
async def get_status():
    """Check how many tasks are waiting for the AI workers."""
    return {"pending_tasks": broker.get_queue_length()}