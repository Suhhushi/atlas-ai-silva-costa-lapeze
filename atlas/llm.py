import requests
import json
from typing import List, Dict, Generator

class OllamaClient:
    def __init__(self, model_name: str = "qwen3:4b-instruct-2507-q4_K_M", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.chat_endpoint = f"{self.base_url}/api/chat"

    def chat_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True
        }

        try:
            with requests.post(self.chat_endpoint, json=payload, stream=True) as response:
                response.raise_for_status()
                
                # On lit la réponse ligne par ligne
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode('utf-8'))
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                            
        except requests.exceptions.ConnectionError:
            yield "Erreur : Impossible de joindre Ollama."
        except Exception as e:
            yield f"Une erreur inattendue est survenue : {e}"


if __name__ == "__main__":
    print("Lancement du prototype ATLAS (Tapez 'quit' pour arrêter)\n")
    
    client = OllamaClient(model_name="qwen3:4b-instruct-2507-q4_K_M")
    
    # Création de la mémoire
    historique: List[Dict[str, str]] = []
    
    while True:
        # Saisie utilisateur
        user_input = input("\n Vous : ")
        if user_input.lower() in ['quit', 'exit', 'quitter']:
            print("Au revoir !")
            break
            
        # Ajout de la question à l'historique
        historique.append({"role": "user", "content": user_input})
        
        print("ATLAS : ", end="", flush=True)
        full_response = ""
        
        # Appel à l'API et affichage en streaming
        for chunk in client.chat_stream(historique):
            print(chunk, end="", flush=True)
            full_response += chunk           

        print()
        
        historique.append({"role": "assistant", "content": full_response})