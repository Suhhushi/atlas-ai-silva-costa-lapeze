# 🏢 ATLAS Consulting — Assistant IA On-Premise

## 🎯 Objectif du projet

Ce projet consiste à développer un prototype d'assistant IA **100% local** pour les collaborateurs du cabinet ATLAS Consulting.

En raison d'exigences de confidentialité strictes (clients santé et bancaires), ce projet n'utilise **aucune API Cloud** (ni OpenAI, ni Anthropic, etc.). L'objectif est de fournir un outil interne capable de :

- Répondre aux questions techniques des consultants.
- Mémoriser le contexte des conversations (historique).
- Filtrer les données sensibles pour éviter toute fuite (Guardrails).
- Monitorer l'utilisation de l'assistant (métriques).

## 🛠️ Prérequis

- Python 3.10+
- Git
- [Ollama](https://ollama.com/) (pour faire tourner le modèle LLM en local)
- Docker (recommandé)

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


# pip install e . fonctionnement :

`pip install -e .` permet d'installer un projet en mode éditable.

Ce que la commande dit :

. -> designe le dossier courant

-e -> signifie éditable

pip crée un lien vers le code source.

Toute modification dans le code est immédiatement reflétée sans réinstaller le package.
```

# fichier pyproject.toml :

[build-system] : Indique à pip les outils à utiliser pour "construire" et installer ton package (ici, setuptools).

[project] : Les métadonnées de ton projet (nom, version, description).

dependencies : C'est ici que tu listes les bibliothèques externes dont ton code a besoin. Pour l'instant, j'ai mis requests (indispensable pour appeler Ollama en local), pydantic et python-dotenv qui sont des standards pour ce type de projet. Tu pourras en ajouter d'autres plus tard !

👥 L'équipe (Binôme)

[Silva Costa José] : Focus sur l'intégration du LLM (llm.py) et la gestion de l'historique (memory.py).

[Lapeze Foucault] : Focus sur la sécurité (guardrails.py) et la remontée des métriques d'utilisation (monitoring.py).
