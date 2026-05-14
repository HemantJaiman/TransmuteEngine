from pydantic import BaseModel, Field

class TranslatedCodeOutput(BaseModel):
    """
    This forces the LLM to output pure code without conversational filler.
    """
    file_name: str = Field(description="The name of the file being translated")
    target_language: str = Field(description="The language we are translating into")
    source_code: str = Field(description="The raw translated code, ready to compile")
    explanation: str = Field(description="A brief summary of what was changed")