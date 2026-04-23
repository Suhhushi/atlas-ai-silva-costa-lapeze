from dotenv import load_dotenv
import requests
import json
from typing import List, Dict, Generator
import argparse
import sys

from atlas.monitoring import LLMJudge

from atlas.monitoring import LLMJudge

load_dotenv()

from atlas.guardrails import Guardrails
from atlas.memory import ConversationMemory, VectorMemory
from langfuse import get_client, propagate_attributes, observe

langfuse = get_client()

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


def main():
    parser = argparse.ArgumentParser(description="ATLAS AI - Assistant conversationnel")
    parser.add_argument("-m", "--model", type=str, default="qwen3:4b-instruct-2507-q4_K_M")
    parser.add_argument("--url", type=str, default="http://localhost:11434")
    args = parser.parse_args()

    print(f" Lancement du prototype ATLAS (Modèle: {args.model})")
    print("Tapez 'quit', 'exit' ou 'quitter' pour arrêter le chat.\n")
    
    # Initialisation
    client = OllamaClient(model_name=args.model, base_url=args.url)
    guard = Guardrails(llm_client=client) 
    vector_db = VectorMemory()
    conv_memory = ConversationMemory()
    
    judge = LLMJudge(llm_client=client)
    
    while True:
        try:
            user_input = input("\n Vous : ")
            if user_input.lower() in ['quit', 'exit', 'quitter']:
                print(" Au revoir !")
                break
                
            if not user_input.strip():
                continue

            # Sécurité
            safe_input = guard.process_input(user_input)
            
            # Mémoire RAG
            souvenirs = vector_db.search_memories(safe_input)

            # Flag si ia utilise memoire
            if souvenirs:
                print("[Souvenirs trouvés dans ChromaDB]")
                tags_pour_langfuse = ["RAG-Actif"]
            else:
                tags_pour_langfuse = []

            # Préparation du prompt
            prompt_enrichi = conv_memory.build_prompt_with_context(safe_input, souvenirs)
            messages_pour_llm = conv_memory.get_history() + [{"role": "user", "content": prompt_enrichi}]
        
            # Génération
            print(" ATLAS : ", end="", flush=True)
            full_response = ""
            trace_id = None

            with propagate_attributes(tags=tags_pour_langfuse):
                for chunk in client.chat_stream(messages_pour_llm):
                    print(chunk, end="", flush=True)
                    full_response += chunk           
                print() 

            # Sauvegardes
            conv_memory.add_message("user", safe_input)
            conv_memory.add_message("assistant", full_response)
            vector_db.save_interaction(safe_input, full_response)
            
            # Monitoring
            trace_id = langfuse.get_current_trace_id()
            judge.evaluate_response(safe_input, full_response, trace_id)
            
        except ValueError as e:
            print(f"\n BLOCAGE SÉCURITÉ : {e}")    
        except KeyboardInterrupt:
            print("\n Arrêt de l'assistant. Au revoir !")
            break
        except Exception as e:
            print(f"\n Une erreur est survenue : {e}")
            
    # On vide la file d'attente Langfuse proprement à la fermeture
    judge.flush()

if __name__ == "__main__":
    main()