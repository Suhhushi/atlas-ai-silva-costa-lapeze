from http import client
from dotenv import load_dotenv
import requests
import json
from typing import List, Dict, Generator
import argparse
import sys

load_dotenv()

from atlas.config import load_config
from atlas.monitoring import LLMJudge
from atlas.guardrails import Guardrails
from atlas.memory import ConversationMemory, VectorMemory

from langfuse import observe, get_client, propagate_attributes
langfuse = get_client()

class OllamaClient:
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434", 
                 temperature: float = 0.3, top_p: float = 0.9, num_ctx: int = 4096):
        self.model_name = model_name
        self.base_url = base_url
        self.temperature = temperature
        self.top_p = top_p
        self.num_ctx = num_ctx
        self.chat_endpoint = f"{self.base_url}/api/chat"
        self.last_input_tokens = 0
        self.last_output_tokens = 0

    def chat_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_ctx": self.num_ctx
            }
        }

        try:
            with requests.post(self.chat_endpoint, json=payload, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode('utf-8'))
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]

                        if data.get("done") == True:
                            self.last_input_tokens = data.get("prompt_eval_count", 0)
                            self.last_output_tokens = data.get("eval_count", 0)
                            
        except requests.exceptions.ConnectionError:
            yield "Erreur : Impossible de joindre Ollama."
        except Exception as e:
            yield f"Une erreur inattendue est survenue : {e}"

@observe(as_type="generation")
def ollama_completion(messages_pour_llm, client):
    # inputs
    langfuse.update_current_generation(
        input=messages_pour_llm,
        model=client.model_name
    )

    print(f" {client.persona_name} : ", end="", flush=True)
    full_response = ""
    
    # Stream
    for chunk in client.chat_stream(messages_pour_llm):
        print(chunk, end="", flush=True)
        full_response += chunk           
    print() 

    # outputs et tokens 
    langfuse.update_current_generation(
        output=full_response,
        usage_details={
            "input": client.last_input_tokens,
            "output": client.last_output_tokens
        }
    )

    return full_response, langfuse.get_current_trace_id()

@observe()
def chat_turn(user_input, guard, vector_db, conv_memory, client, judge, config):
    # Sécurité
    if config.guardrails.enabled:
        safe_input = guard.process_input(user_input)
    else:
        safe_input = user_input

    souvenirs = vector_db.search_memories(
        safe_input, 
        n_results=config.memory.top_k,
        distance_threshold=config.memory.min_similarity
    )
    
    # Mémoire RAG
    souvenirs = vector_db.search_memories(safe_input)
    tags_pour_langfuse = ["RAG-Actif"] if souvenirs else []
    
    if souvenirs:
        print("   [ Souvenirs trouvés dans ChromaDB]")

    # Préparation du prompt
    prompt_enrichi = conv_memory.build_prompt_with_context(safe_input, souvenirs)

    system_message = [{"role": "system", "content": config.persona.system_prompt}]
    messages_pour_llm = system_message + conv_memory.get_history() + [{"role": "user", "content": prompt_enrichi}]

    # Appel à la génération
    with propagate_attributes(tags=tags_pour_langfuse):
        full_response, trace_id = ollama_completion(messages_pour_llm, client)

    # Sauvegardes
    conv_memory.add_message("user", safe_input)
    conv_memory.add_message("assistant", full_response)
    vector_db.save_interaction(safe_input, full_response)
    
    # Monitoring : Évaluation
    if trace_id:
        judge.evaluate_response(safe_input, full_response, trace_id)


def main():
    config = load_config()

    parser = argparse.ArgumentParser(description="ATLAS AI - Assistant conversationnel")
    parser.add_argument("-m", "--model", type=str, default=config.model.name)
    parser.add_argument("--url", type=str, default="http://localhost:11434")
    args = parser.parse_args()

    print(f" Lancement du prototype ATLAS (Modèle: {args.model})")
    print("Tapez 'quit', 'exit' ou 'quitter' pour arrêter le chat.\n")
    
    client = OllamaClient(
        model_name=args.model, 
        base_url=args.url,
        temperature=config.model.temperature,
        top_p=config.model.top_p,
        num_ctx=config.model.num_ctx
    )
    client.persona_name = config.persona.name
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

            chat_turn(user_input, guard, vector_db, conv_memory, client, judge, config)  

        except ValueError as e:
            print(f"\n BLOCAGE SÉCURITÉ : {e}")    
        except KeyboardInterrupt:
            print("\n Arrêt de l'assistant. Au revoir !")
            break
        except Exception as e:
            print(f"\n Une erreur est survenue : {e}")
            
    langfuse.flush()
    judge.flush()

if __name__ == "__main__":
    main()