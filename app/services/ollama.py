import logging
from typing import Optional, List, AsyncGenerator
import httpx
from httpx import Timeout

from app.config import settings
from app.exceptions import OllamaError

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.default_model = settings.DEFAULT_MODEL
        self.timeout = Timeout(settings.OLLAMA_TIMEOUT)
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def generate_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        context: Optional[List[str]] = None,
        stream: bool = False
    ) -> AsyncGenerator[str, None]:
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
            if stream:
                async with self.client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": full_prompt,
                        "stream": True,
                        "context": context
                    }
                ) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_lines():
                        if chunk.strip():
                            yield chunk
            else:
                response = await self.client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": full_prompt,
                        "stream": False,
                        "context": context
                    }
                )
                response.raise_for_status()
                data = response.json()
                yield data.get("response", "")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error: {str(e)}")
            raise OllamaError(f"API request failed: {str(e)}")
        except httpx.RequestError as e:
            logger.error(f"Ollama connection error: {str(e)}")
            raise OllamaError(f"Connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected Ollama error: {str(e)}")
            raise OllamaError(f"Unexpected error: {str(e)}")

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

# Example usage:
# async with OllamaService() as ollama:
#     async for chunk in ollama.generate_response("Hello", stream=True):
#         print(chunk)