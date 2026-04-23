from langfuse import get_client

langfuse_client = get_client()

class LLMJudge:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def evaluate_response(self, question: str, response: str, trace_id: str):
        if not trace_id:
            return

        prompt = f"""Tu es un juge strict. Note de 0.0 à 1.0 la pertinence de cette réponse.
        Question : {question}
        Réponse : {response}
        Réponds UNIQUEMENT par le nombre décimal (ex: 0.8), aucun autre mot."""
        
        print("   [Évaluation en cours...]", end="", flush=True)
        score_brut = ""
        
        try:
            # LLM génère la note
            for chunk in self.llm_client.chat_stream([{"role": "user", "content": prompt}]):
                score_brut += chunk
            
            # Nettoyage
            score_str = ''.join(c for c in score_brut if c.isdigit() or c == '.')
            
            # Sécurité
            if not score_str:
                raise ValueError(f"Aucun chiffre renvoyé par l'IA. Réponse brute : '{score_brut}'")
                
            score_float = float(score_str)
            score_float = min(max(score_float, 0.0), 1.0)
            
            langfuse_client.create_score(
                trace_id=trace_id, 
                name="qualite_reponse", 
                value=score_float,
                comment="Évalué localement par Ollama",
                data_type="NUMERIC"
            )
            print(f" -> Note : {score_float}/1.0]")
            
        except Exception as e:
            print(f" -> Échec  (Raison : {e})")
            
    def flush(self):
        langfuse_client.flush()