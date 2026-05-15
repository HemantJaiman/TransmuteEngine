import os
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import redis
import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import shutil

# Import Phase 1 & 2 Logic
from ingestion.graph import DependencyGraph
from queues.broker import TaskBroker
from core_agents.models import ModelFactory

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

        # Clear the old queue before starting a new run
        broker.client.delete(broker.queue_name)
        
        # Step 3: Package metadata and push to Redis (Phase 2)
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
        
        # --- THE FIX: Safely format the execution order for the browser ---
        safe_execution_order = []
        for item in migration_order:
            if isinstance(item, list):
                safe_execution_order.append("SCC BUNDLE: " + " + ".join([os.path.basename(f) for f in item]))
            else:
                safe_execution_order.append(os.path.basename(item))

        return {
            "status": "success",
            "message": "Codebase mapped. Tasks pushed to AI Swarm.",
            "total_files": tasks_queued,
            "execution_order": safe_execution_order
        }

    except ValueError as ve:
        # Catching Circular Dependencies from Phase 1
        raise HTTPException(status_code=422, detail=f"Graph Error: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", 6379)), decode_responses=True)
    pubsub = r.pubsub()
    pubsub.subscribe("swarm_logs")
    
    loop_count = 0
    try:
        while True:
            message = pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                await websocket.send_text(message["data"])
            
            # Ping only once every 50 loops (5 seconds)
            loop_count += 1
            if loop_count % 50 == 0:
                await websocket.send_json({"message": "ping", "type": "ping"})
                
            await asyncio.sleep(0.1) 
    except WebSocketDisconnect:
        pubsub.close()

class GuideRequest(BaseModel):
    target_directory: str = "modernized_codebase"
    target_stack: str
    custom_instructions: str
    model_choice: str

@app.post("/api/v1/generate_guide")
async def generate_guide(request: GuideRequest):
    """Scans the completed migration and generates a setup guide."""
    if not os.path.exists(request.target_directory):
        raise HTTPException(status_code=400, detail="Modernized codebase not found.")

    try:
        # Get a list of the newly generated files
        files_generated = os.listdir(request.target_directory)
        
        prompt = f"""
        You are a Staff Software Engineer. You just led a migration to {request.target_stack}.
        The following files were generated: {', '.join(files_generated)}
        
        User Constraints applied during migration: {request.custom_instructions}
        
        Write a concise, professional MIGRATION_GUIDE.md.
        Include:
        1. Prerequisites (e.g., Node version, Python version).
        2. Exact installation commands (e.g., npm install, pip install).
        3. How to start the development server.
        4. Any manual steps the developer might still need to do (e.g., setup database passwords).
        
        Output ONLY the markdown content. No conversational filler.
        """

        # Fetch the model and generate the guide
        model = ModelFactory.get_model(request.model_choice)
        
        if request.model_choice == "gemini":
            response = model.generate_content(prompt)
            guide_content = response.text
        else:
            response = model.beta.chat.completions.parse(
                model=request.model_choice if request.model_choice != "gpt4" else "gpt-4o-2024-08-06",
                messages=[{"role": "user", "content": prompt}]
            )
            guide_content = response.choices[0].message.content

        # Write the guide to the modernized folder
        guide_path = os.path.join(request.target_directory, "MIGRATION_GUIDE.md")
        with open(guide_path, "w", encoding="utf-8") as f:
            f.write(guide_content)

        # Broadcast the success to the UI via Redis
        r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", 6379)))
        r.publish("swarm_logs", json.dumps({"message": "✨ MIGRATION_GUIDE.md generated successfully!", "type": "success"}))

        return {"status": "success", "message": "Guide generated."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/download")
async def download_codebase():
    """Zips the finalized codebase and sends it to the user."""
    target_dir = "modernized_codebase"
    
    if not os.path.exists(target_dir):
        raise HTTPException(status_code=404, detail="Codebase not found. Has a migration completed?")
    
    # Create a zip archive named 'modernized_codebase.zip'
    zip_path = shutil.make_archive("modernized_codebase", 'zip', target_dir)
    
    # Return it to the browser as a downloadable file
    return FileResponse(zip_path, filename="modernized_codebase.zip", media_type="application/zip")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)