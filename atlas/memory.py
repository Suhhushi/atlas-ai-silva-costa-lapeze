import chromadb
import uuid
from typing import List, Dict

class VectorMemory:
    # Gère la mémoire long terme
    def __init__(self, persist_directory: str = "./data/memory"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection("conversations")

    def save_interaction(self, question: str, response: str, metadata: dict = None):
        """Sauvegarde avec gestion des tags métier en bonus[cite: 1]."""
        doc_id = str(uuid.uuid4())
        document = f"Question: {question}\nRéponse: {response}"
        
        # Tag par défaut si aucun fourni
        meta = metadata if metadata else {"type": "qa_pair", "topic": "general"}
        
        self.collection.add(
            documents=[document],
            metadatas=[meta],
            ids=[doc_id]
        )

    def search_memories(self, query: str, n_results: int = 2, distance_threshold: float = 1.2, filter_metadata: dict = None) -> List[str]:
        """Cherche un souvenir pertinent en filtrant par distance et par tag."""
        if self.collection.count() == 0:
            return []
            
        query_params = {
            "query_texts": [query],
            "n_results": min(n_results, self.collection.count())
        }
        if filter_metadata:
            query_params["where"] = filter_metadata
            
        results = self.collection.query(**query_params)
        
        valid_memories = []
        if results['documents'] and results['documents'][0]:
            for doc, distance in zip(results['documents'][0], results['distances'][0]):
                if distance < distance_threshold: 
                    valid_memories.append(doc)
                    
        return valid_memories

    def forget(self, query: str) -> bool:
        """Bonus : Implémente l'oubli d'un souvenir spécifique[cite: 1]."""
        if self.collection.count() == 0:
            return False

        # cherche le souvenir qui correspond le plus à la demande
        results = self.collection.query(
            query_texts=[query],
            n_results=1
        )

        if results['ids'] and results['ids'][0]:
            doc_id_to_delete = results['ids'][0][0]
            self.collection.delete(ids=[doc_id_to_delete])
            return True
        return False


class ConversationMemory:
    # Gère mémoire à court terme
    def __init__(self, summarize_every_n: int = 5):
        self.messages: List[Dict[str, str]] = []
        self.summarize_every_n = summarize_every_n
        self.turn_count = 0

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        if role == "user":
            self.turn_count += 1

    def get_history(self) -> List[Dict[str, str]]:
        return self.messages

    def build_prompt_with_context(self, question: str, long_term_memories: List[str]) -> str:
        if not long_term_memories:
            return question
            
        context_block = "\n".join([f"- {mem}" for mem in long_term_memories])
        
        prompt = f"""Voici le contexte de nos discussions passées strictement pertinent pour ta réponse :
{context_block}

Nouvelle question : {question}"""
        return prompt

    def needs_summary(self) -> bool:
        """Vérifie si on a atteint le nombre N de tours pour résumer[cite: 1]."""
        return self.turn_count >= self.summarize_every_n

    def generate_summary(self, llm_client) -> str:
        """Bonus : Fait appel au LLM pour condenser l'historique[cite: 1]."""
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in self.messages])
        prompt = "Fais un résumé très concis (2-3 phrases max) des informations importantes de cette conversation pour t'en souvenir plus tard."
        
        messages = [
            {"role": "system", "content": "Tu es un expert en synthèse."},
            {"role": "user", "content": f"{prompt}\n\nHistorique :\n{history_text}"}
        ]
        
        summary = ""
        # utilise client LLM existant
        for chunk in llm_client.chat_stream(messages):
            summary += chunk
            
        # vide mémoire courte pour libérer le contexte
        self.messages = []
        self.turn_count = 0
        return summary