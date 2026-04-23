import chromadb
import uuid
from typing import List, Dict

class VectorMemory:
    # Gère la mémoire à long terme
    def __init__(self, persist_directory: str = "./data/memory"):

        # Initialise ChromaDB
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection("conversations")

    def save_interaction(self, question: str, response: str):
        # Sauvegarde une paire Question/Réponse.
        
        doc_id = str(uuid.uuid4())
        document = f"Question: {question}\nRéponse: {response}"
        
        self.collection.add(
            documents=[document],
            ids=[doc_id]
        )

    def search_memories(self, query: str, n_results: int = 2) -> List[str]:
        # Cherche souvenir.
        if self.collection.count() == 0:
            return []
            
        results = self.collection.query(
            query_texts=[query],
            n_results=min(n_results, self.collection.count())
        )
        
        # Retourne la liste des documents trouvés
        if results['documents'] and results['documents'][0]:
            return results['documents'][0]
        return []

class ConversationMemory:
    # Gère la mémoire à court terme
    def __init__(self):
        self.messages: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def get_history(self) -> List[Dict[str, str]]:
        return self.messages

    def build_prompt_with_context(self, question: str, long_term_memories: List[str]) -> str:
        if not long_term_memories:
            return question
            
        context_block = "\n".join([f"- {mem}" for mem in long_term_memories])
        
        prompt = f"""Voici quelques notes de nos conversations passées qui pourraient t'aider : {context_block} Utilise ces informations si elles sont pertinentes pour répondre à la nouvelle question. Nouvelle question : {question}"""
        
        return prompt