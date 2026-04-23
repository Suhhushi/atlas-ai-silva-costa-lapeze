import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("atlas.guardrails")

class Guardrails:
    def __init__(self, llm_client=None, config: dict = None):
        self.llm_client = llm_client
        self.config = config or {
            "enabled": True,
            "max_words": 150,
            "blocked_topics": ["politique", "religion"],
            "pii_patterns": {
                "credit_card": r"\b(?:\d[ -]*?){13,16}\b"
            },
            "injection_patterns": ["ignore previous instructions", "oublie toutes les instructions", "<|system|>"]
        }

    def _check_length(self, text: str) -> bool:
        """Règle 1 : Limitation de longueur[cite: 1]"""
        if len(text.split()) > self.config["max_words"]:
            logger.warning("Guardrail déclenché : Requête trop longue.")
            raise ValueError(f"Requête trop longue (limite : {self.config['max_words']} mots).")
        return True

    def _check_topics(self, text: str) -> bool:
        """Règle 2 : Blocage de sujets interdits (Recherche stricte)[cite: 1]"""
        text_lower = text.lower()
        for topic in self.config["blocked_topics"]:
            pattern = rf"\b{re.escape(topic)}\b"
            if re.search(pattern, text_lower):
                logger.warning(f"Guardrail déclenché : Sujet interdit ({topic}).")
                raise ValueError("Je suis un assistant professionnel, je ne peux pas aborder ce sujet.")
        return True

    def _check_injection(self, text: str) -> bool:
        """Règle 3 : Détection de prompt injection[cite: 1]"""
        text_lower = text.lower()
        for pattern in self.config["injection_patterns"]:
            if pattern in text_lower:
                logger.warning("Guardrail déclenché : Tentative de prompt injection.")
                raise ValueError("Requête non autorisée : tentative de manipulation des instructions systémes.")
        return True

   # LLM check la coorélation entre le prompt et les topics bloqué
    def _check_semantics_with_llm(self, text: str) -> bool:
        """Règle Avancée : Compréhension sémantique via le LLM"""
        if not self.llm_client:
            return True 
            
        sujets = ", ".join(self.config["blocked_topics"])
        
        moderator_prompt = f"""Tu es un automate de classification. Ton seul but est de dire si un texte appartient à une catégorie.
Catégories interdites : {sujets}.

Règles :
1. Si le texte parle des catégories interdites, de partis politiques, d'élections, de figures politiques ou de religions, tu dois répondre EXACTEMENT et SEULEMENT le mot : BLOQUER.
2. Sinon, tu dois répondre EXACTEMENT et SEULEMENT le mot : AUTORISER.
3. Ne justifie pas. Ne fais pas de phrase.

Texte à analyser : "{text}"
Classification :"""

        messages = [{"role": "user", "content": moderator_prompt}]

        try:
            response = ""
            logger.debug(f"Analyse sémantique en cours pour : '{text}'")
            
            for chunk in self.llm_client.chat_stream(messages):
                response += chunk
            
            clean_response = response.strip().upper()
            logger.info(f"Verdict du LLM-Juge : '{clean_response}'")
            
            if "BLOQUER" in clean_response:
                logger.warning("Guardrail Sémantique déclenché : Le LLM a détecté un contexte interdit.")
                raise ValueError("Je suis un assistant professionnel, je détecte que ce sujet sort de mon périmètre.")
                
        except Exception as e:
            if isinstance(e, ValueError):
                raise e
            logger.error(f"Erreur lors de la vérification sémantique : {e}")
            
        return True

    #pii : information perso
    def _mask_pii(self, text: str) -> str:
        """Règle 4 : Détection et masquage de PII[cite: 1]"""
        masked_text = text
        for name, pattern in self.config["pii_patterns"].items():
            if re.search(pattern, masked_text):
                logger.info(f"Guardrail déclenché : Masquage de {name}.")
                masked_text = re.sub(pattern, "[DONNÉE_MASQUÉE]", masked_text)
        return masked_text

    def process_input(self, user_input: str) -> str:
        """Applique toutes les règles avant l'envoi au LLM."""
        if not self.config["enabled"]:
            return user_input

        self._check_length(user_input)
        self._check_topics(user_input)
        self._check_injection(user_input)
        self._check_semantics_with_llm(user_input)

        return self._mask_pii(user_input)