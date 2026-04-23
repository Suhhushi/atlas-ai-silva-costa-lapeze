from langfuse import Langfuse

langfuse_client = Langfuse()

class LLMJudge:
    def __init__(self, llm_client):
        """
        Prend en paramètre un client LLM pour l'utiliser comme juge.
        """
        self.llm_client = llm_client

    def evaluate_response(self, question: str, response: str, trace_id: str):
        """Demande à Ollama de noter la réponse et envoie le score à Langfuse."""
        if not trace_id:
            return

        prompt = f"""Tu es un juge strict. Note de 0.0 à 1.0 la pertinence de cette réponse.
        Question : {question}
        Réponse : {response}
        Réponds UNIQUEMENT par le nombre décimal (ex: 0.8), aucun autre mot."""
        
        print("   [Évaluation]", end="", flush=True)
        score_brut = ""
        
        # le client LLM pour génère la note
        try:
            for chunk in self.llm_client.chat_stream([{"role": "user", "content": prompt}]):
                score_brut += chunk
            
            # netoyage de la reponse
            score_float = float(''.join(c for c in score_brut if c.isdigit() or c == '.'))
            score_float = min(max(score_float, 0.0), 1.0)
            
            # envoie du score 
            langfuse_client.score(
                trace_id=trace_id, 
                name="qualite_reponse", 
                value=score_float,
                comment="Évalué localement par Ollama"
            )
            print(f" -> Note : {score_float}/1.0]")
            
        except Exception:
            print(" -> Échec (le juge a mal formaté sa note)]")
            
    def flush(self):
        """S'assure que toutes les données sont bien envoyées à Langfuse avant de quitter."""
        langfuse_client.flush()