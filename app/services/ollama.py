import requests
from typing import List, Dict

from app.config import settings

class OllamaService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.default_model = settings.DEFAULT_MODEL

    def generate_response(self, prompt: str, model: str = None, context: List[str] = None):
        model = model or self.default_model
        context_text = "\n\n".join(context) if context else ""
        
        full_prompt = f"""
        Context information is below.
        ---------------------
        {context_text}
        ---------------------
        Given the context information and not prior knowledge, answer the query.
        Query: {prompt}
        Answer:
        """
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling Ollama: {str(e)}")
