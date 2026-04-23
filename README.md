# 🏢 ATLAS Consulting — Assistant IA On-Premise

## 🎯 Objectif du projet
Ce projet consiste à développer un prototype d'assistant IA **100% local** pour les collaborateurs du cabinet ATLAS Consulting. 

En raison d'exigences de confidentialité strictes (clients santé et bancaires), ce projet n'utilise **aucune API Cloud** (ni OpenAI, ni Anthropic, etc.). L'objectif est de fournir un outil interne capable de :
* Répondre aux questions techniques des consultants.
* Mémoriser le contexte des conversations (historique).
* Filtrer les données sensibles pour éviter toute fuite (Guardrails).
* Monitorer l'utilisation de l'assistant (métriques).

## 🛠️ Prérequis

* Python 3.10+
* Git
* [Ollama](https://ollama.com/) (pour faire tourner le modèle LLM en local)
* Docker (recommandé)

## 🚀 Comment lancer le projet

```bash
# Cloner le dépôt :

git clone <URL_DU_REPO>
cd atlas-ai-<votre-nom>

# Installer les dépendances :

# Si vous utilisez un environnement virtuel (recommandé)
python -m venv venv
venv\Scripts\activate

# Installation via requirements.txt ou pyproject.toml

pip install -r requirements.txt 

# ou si pyproject.toml : pip install .
3. Lancer le service LLM (Ollama) :

# S'assurer que Ollama tourne en arrière-plan, puis télécharger le modèle choisi (ex: Mistral ou Llama3)
ollama pull mistral

# Démarrer l'assistant :
# Lancer le point d'entrée principal (à adapter selon la suite du TP)
python scripts/main.py
```

👥 L'équipe (Binôme)

[Lapeze Foucault] : Focus sur l'intégration du LLM (llm.py) et la gestion de l'historique (memory.py).

[Silva Costa José] : Focus sur la sécurité (guardrails.py) et la remontée des métriques d'utilisation (monitoring.py).