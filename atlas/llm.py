import requests
import json
from typing import List, Dict, Generator
import argparse
import sys

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


def main():
    parser = argparse.ArgumentParser(
        description="ATLAS AI - Assistant conversationnel 100% on-premise"
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default="qwen3:4b-instruct-2507-q4_K_M",
        help="Le nom du modèle Ollama à utiliser"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:11434",
        help="L'URL de l'API Ollama"
    )
    
    args = parser.parse_args()

    print(f"Lancement du prototype ATLAS (Modèle: {args.model})")
    print("Tapez 'quit', 'exit' ou 'quitter' pour arrêter le chat.\n")
    
    # Initialisation avec les paramètres de la CLI
    client = OllamaClient(model_name=args.model, base_url=args.url)
    historique = []
    
    while True:
        try:
            user_input = input("\n Vous : ")
            if user_input.lower() in ['quit', 'exit', 'quitter']:
                print("Au revoir !")
                break
                
            if not user_input.strip():
                continue
                
            historique.append({"role": "user", "content": user_input})
            
            print("ATLAS : ", end="", flush=True)
            full_response = ""
            
            # Affichage en streaming
            for chunk in client.chat_stream(historique):
                print(chunk, end="", flush=True)
                full_response += chunk           

            print() 
            historique.append({"role": "assistant", "content": full_response})
            
        except KeyboardInterrupt:
            print("\nArrêt de l'assistant. Au revoir !")
            break
        except Exception as e:
            print(f"\n Une erreur est survenue : {e}")

if __name__ == "__main__":
    main()