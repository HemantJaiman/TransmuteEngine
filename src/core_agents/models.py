import os
from openai import OpenAI
import google.generativeai as genai

class ModelFactory:
    """
    A centralized hub to fetch the AI model the user requested.
    This keeps our workflow code clean and model-agnostic.
    """
    @staticmethod
    def get_model(choice: str):
        if choice == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in .env file")
            genai.configure(api_key=api_key)
            return genai.GenerativeModel('gemini-2.5-flash')
        
        elif choice == "gpt4":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in .env file")
            return OpenAI(api_key=api_key)
            
        elif choice == "llama3":
            # Points to your local Ollama instance (Free)
            return OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
            
        raise ValueError(f"Model '{choice}' is not supported yet.")