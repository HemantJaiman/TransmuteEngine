import os
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import redis

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import Phase 1 & 2 Logic
from ingestion.graph import DependencyGraph
from queues.broker import TaskBroker

# Load environment variables (API keys, Redis config)
load_dotenv()

app = FastAPI(
    title="Transmute Engine Orchestrator",
    description="Enterprise-grade AI Migration Framework"
)
app.mount("/static", StaticFiles(directory="static"), name="static")
broker = TaskBroker()

class MigrationRequest(BaseModel):
    target_directory: str
    target_stack: str           # e.g., "FastAPI and Vue 3"
    custom_instructions: str    # e.g., "Use functional components only, no classes"
    model_choice: str           # e.g., "gemini", "gpt4", or "llama3"


@app.get("/")
async def serve_ui():
    """Serves the Transmute Engine UI on the main route."""
    return FileResponse("static/index.html")


@app.get("/api/v1/status")
async def get_status():
    """Returns the current number of tasks waiting in the Redis queue."""
    try:
        return {"pending_tasks": broker.get_queue_length()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis Error: {str(e)}")

@app.post("/api/v1/migrate")
async def start_migration(request: MigrationRequest):
    """
    1. Triggers AST parsing and Dependency Mapping.
    2. Calculates the mathematically correct migration order.
    3. Pushes context-aware tasks into the Redis queue for the AI Swarm.
    """
    if not os.path.exists(request.target_directory):
        raise HTTPException(status_code=400, detail="Target directory does not exist.")

    try:
        # Step 1: Initialize Ingestion Engine (Phase 1)
        engine = DependencyGraph(request.target_directory)
        engine.build_graph()
        
        # Step 2: Calculate Topological Sort Order
        migration_order = engine.get_migration_order()
        
        # Step 3: Package metadata and push to Redis (Phase 2)
        # We pass the full request so the worker knows the user's AI preferences
        tasks_queued = 0
        for file_path in migration_order:
            task_payload = {
                "file_path": file_path,
                "target_stack": request.target_stack,
                "custom_instructions": request.custom_instructions,
                "model_choice": request.model_choice
            }
            broker.push_task(task_payload)
            tasks_queued += 1
        
        return {
            "status": "success",
            "message": "Codebase mapped. Tasks pushed to AI Swarm.",
            "total_files": tasks_queued,
            "execution_order": [os.path.basename(f) for f in migration_order]
        }

    except ValueError as ve:
        # Catching Circular Dependencies from Phase 1
        raise HTTPException(status_code=422, detail=f"Graph Error: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """Streams live AI Worker logs to the Cockpit UI via Redis Pub/Sub."""
    await websocket.accept()
    
    # Connect to Redis
    r = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"), 
        port=int(os.getenv("REDIS_PORT", 6379)), 
        decode_responses=True
    )
    pubsub = r.pubsub()
    pubsub.subscribe("swarm_logs")
    
    try:
        while True:
            # Check for new messages from the AI Worker
            message = pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                await websocket.send_text(message["data"])
            
            # Yield control back to the event loop so the server doesn't freeze
            await asyncio.sleep(0.1) 
    except WebSocketDisconnect:
        pubsub.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)