import json
import os
import redis

class TaskBroker:
    def __init__(self):
        # Tier-1 Practice: Always pull infrastructure config from the environment
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", 6379))
        
        self.client = redis.Redis(host=host, port=port, decode_responses=True)
        self.queue_name = "migration_tasks"

    def push_task(self, task_payload: dict):
        """Pushes a context-aware task to the AI Swarm queue."""
        self.client.rpush(self.queue_name, json.dumps(task_payload))

    def get_queue_length(self):
        return self.client.llen(self.queue_name)