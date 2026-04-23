import requests
import json
from typing import List, Dict, Generator
from langfuse.decorators import observe

class OllamaClient:
    def __init__(self, model_name: str = "qwen3:4b-instruct-2507-q4_K_M", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.chat_endpoint = f"{self.base_url}/api/chat"

    @observe(name="atlas_chat")
    def chat_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True
        }

        try:
            with requests.post(self.chat_endpoint, json=payload, stream=True) as response:
                response.raise_for_status()
                
                # Lit la réponse ligne par ligne
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode('utf-8'))
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                            
        except requests.exceptions.ConnectionError:
            yield "Erreur : Impossible de joindre Ollama."
        except Exception as e:
            yield f"Une erreur inattendue est survenue : {e}"