from typing import TypedDict, Optional

class MigrationState(TypedDict):
    # Core File Data
    file_path: str
    legacy_code: str
    translated_code: Optional[str]
    
    # User Preferences (New)
    target_stack: str           # e.g., "FastAPI and React"
    custom_instructions: str    # e.g., "Don't use classes"
    model_choice: str           # e.g., "gemini" or "llama3"
    
    # Execution Tracking
    error_message: Optional[str]
    retry_count: int
    migration_notes: list[str]  # For the "Migration Guide" file later