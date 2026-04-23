import argparse
import sys
from dotenv import load_dotenv
from langfuse import get_client, propagate_attributes
from atlas.llm import OllamaClient
from atlas.guardrails import Guardrails
from atlas.memory import ConversationMemory, VectorMemory
from atlas.monitoring import LLMJudge

load_dotenv()
langfuse = get_client()

def main():
    parser = argparse.ArgumentParser(description="ATLAS AI - Assistant conversationnel")
    parser.add_argument("-m", "--model", type=str, default="qwen3:4b-instruct-2507-q4_K_M")
    parser.add_argument("--url", type=str, default="http://localhost:11434")
    args = parser.parse_args()

    print(f"Lancement du prototype ATLAS (Modèle: {args.model})")
    print("Tapez 'quit' pour arrêter, ou '/forget <sujet>' pour effacer un souvenir.\n")
    
    # Initialisation
    client = OllamaClient(model_name=args.model, base_url=args.url)
    guard = Guardrails(llm_client=client) 
    vector_db = VectorMemory()
    
    # Configuration mémoire courte
    conv_memory = ConversationMemory(summarize_every_n=4) 
    
    judge = LLMJudge(llm_client=client)
    
    while True:
        try:
            user_input = input("\nVous : ")
            if user_input.lower() in ['quit', 'exit', 'quitter']:
                print("Au revoir !")
                break
                
            if not user_input.strip():
                continue

            # Gestion de l'oubli /forget
            if user_input.startswith("/forget "):
                concept_to_forget = user_input.replace("/forget ", "").strip()
                if vector_db.forget(concept_to_forget):
                    print(f"Mémoire effacée concernant : '{concept_to_forget}'")
                else:
                    print("Aucun souvenir correspondant trouvé.")
                continue

            # Sécurité
            safe_input = guard.process_input(user_input)
            
            # Mémoire RAG
            souvenirs = vector_db.search_memories(safe_input, distance_threshold=1.2)

            if souvenirs:
                print("[Souvenirs pertinents trouvés dans ChromaDB]")
                tags_pour_langfuse = ["RAG-Actif"]
            else:
                tags_pour_langfuse = []

            # Préparation du prompt
            prompt_enrichi = conv_memory.build_prompt_with_context(safe_input, souvenirs)
            messages_pour_llm = conv_memory.get_history() + [{"role": "user", "content": prompt_enrichi}]
        
            # Génération
            print("ATLAS : ", end="", flush=True)
            full_response = ""

            with propagate_attributes(tags=tags_pour_langfuse):
                for chunk in client.chat_stream(messages_pour_llm):
                    print(chunk, end="", flush=True)
                    full_response += chunk           
                print() 

            # Sauvegardes et tags métier
            conv_memory.add_message("user", safe_input)
            conv_memory.add_message("assistant", full_response)
            
            # analyse le prompt pour y associer un contexte
            topic_tag = "commercial" if "client" in safe_input.lower() else "general"
            vector_db.save_interaction(safe_input, full_response, metadata={"topic": topic_tag})
            
            if conv_memory.needs_summary():
                print("\n[⚙️ ATLAS synthétise la conversation en arrière-plan...]")
                summary = conv_memory.generate_summary(client)
                vector_db.save_interaction("Résumé de session", summary, metadata={"type": "summary"})
                print("[Synthèse sauvegardée en mémoire longue. Mémoire courte purgée.]")

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
            
    judge.flush()

if __name__ == "__main__":
    main()