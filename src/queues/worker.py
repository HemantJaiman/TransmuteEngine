import json
import os
import redis
from dotenv import load_dotenv
from core_agents.workflow import migration_swarm

load_dotenv()

class SwarmWorker:
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.client = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)
        self.queue_name = "migration_tasks"
        self.broadcast("🤖 AI Worker Node online and listening.", "success")

    def broadcast(self, message: str, msg_type: str = "info"):
        print(message)
        payload = json.dumps({"message": message, "type": msg_type})
        self.client.publish("swarm_logs", payload)

    def listen(self):
        while True:
            result = self.client.blpop(self.queue_name, timeout=0)
            if result:
                _, payload_str = result
                self._process_task(json.loads(payload_str))

    def _process_task(self, task: dict):
        file_path = task.get('file_path')
        
        # --- THE FIX: Handle SCC Bundles ---
        if isinstance(file_path, list):
            # Extract names and join them (e.g., "auth.py + database.py")
            filename = "SCC_BUNDLE: " + " + ".join([os.path.basename(f) for f in file_path])
        else:
            filename = os.path.basename(file_path)
        
        self.broadcast(f"\n=====================================")
        self.broadcast(f"🚀 INITIATING: {filename}")
        self.broadcast(f"🧠 ENGINE: {task.get('model_choice')} | 🎯 TARGET: {task.get('target_stack')}")
        
        initial_state = {
            "file_path": file_path, "legacy_code": "", "translated_code": None,
            "target_stack": task.get('target_stack'), "custom_instructions": task.get('custom_instructions'),
            "model_choice": task.get('model_choice'), "error_message": None, "retry_count": 0, "migration_notes": []
        }
        
        try:
            final_state = migration_swarm.invoke(initial_state)
            
            if final_state and not final_state.get("error_message"):
                self.broadcast(f"✨ SUCCESS: {filename} migrated completely.", "success")
            else:
                self.broadcast(f"💥 FAILED: {filename} failed after retries.", "error")

        except Exception as e:
            self.broadcast(f"💥 CRITICAL ERROR on {filename}: {str(e)}", "error")

if __name__ == "__main__":
    worker = SwarmWorker()
    worker.listen()