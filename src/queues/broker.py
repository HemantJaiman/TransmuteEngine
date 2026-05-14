import json
import redis
from typing import List

class TaskBroker:
    def __init__(self, host='localhost', port=6379):
        # In a real enterprise system, these come from environment variables
        self.client = redis.Redis(host=host, port=port, decode_responses=True)
        self.queue_name = "migration_tasks"

    def push_migration_batch(self, files_to_migrate: List[str]):
        """
        Pushes a list of files into the Redis queue.
        Because of Kahn's Algorithm (Phase 1), we know these files 
        are pushed in the exact mathematical order they must be processed.
        """
        for file_path in files_to_migrate:
            task_payload = {
                "file_path": file_path,
                "status": "pending"
            }
            # Push to the right side of the Redis list
            self.client.rpush(self.queue_name, json.dumps(task_payload))
            
        return len(files_to_migrate)

    def get_queue_length(self):
        return self.client.llen(self.queue_name)