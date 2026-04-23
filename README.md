# ATLAS Consulting — Assistant IA On-Premise

# Objectif du projet

Ce projet consiste à développer un prototype d'assistant IA **100% local** pour les collaborateurs du cabinet ATLAS Consulting.

En raison d'exigences de confidentialité strictes (clients santé et bancaires), ce projet n'utilise **aucune API Cloud** (ni OpenAI, ni Anthropic, etc.). L'objectif est de fournir un outil interne capable de :

- Répondre aux questions techniques des consultants de manière fluide (Streaming).
- Mémoriser le contexte des conversations à court et long terme (RAG).
- Filtrer les données sensibles pour éviter toute fuite via des règles de sécurité strictes (Guardrails).
- Monitorer l'utilisation et évaluer la qualité des réponses de l'assistant (Langfuse + LLM-as-a-Judge).


## Architecture et Fonctionnalités

Le projet est découpé en plusieurs briques métiers indépendantes :

1. **Moteur LLM (`llm.py`)** : Client local communiquant avec l'API REST d'Ollama. Supporte le streaming des réponses et la remontée des tokens consommés.
2. **Mémoire Intelligente (`memory.py`)** : 
   - *Court terme* : Conserve le contexte de la session active et génère un résumé automatique tous les N tours.
   - *Long terme* : Base de données vectorielle (ChromaDB) avec recherche sémantique, filtrage par tags métier, et capacité d'oubli spécifique (commande `/forget`).
3. **Sécurité et Gouvernance (`guardrails.py`)** : Pipeline de validation des requêtes (longueur, blocage de sujets stricts, protection contre les prompt injections, masquage des données personnelles PII) et validation sémantique par un LLM Juge.
4. **Observabilité (`monitoring.py` & Langfuse)** : Traces hiérarchiques de chaque interaction, calcul des coûts/tokens, et notation automatique de la pertinence des réponses (LLM-as-a-judge).

---

## Structure du projet

\`\`\`
atlas-ai/
├── atlas/                 # Code source principal (Package Python)
│   ├── __init__.py
│   ├── cli.py             # Point d'entrée et orchestration
│   ├── guardrails.py      # Règles de sécurité et filtrage
│   ├── llm.py             # Client API Ollama
│   ├── memory.py          # Gestion ChromaDB et historique
│   └── monitoring.py      # LLM Judge pour l'évaluation
├── config/                # Fichiers de configuration
├── data/
│   └── memory/            # Base de données vectorielle locale (ChromaDB)
├── scripts/               # Scripts utilitaires
├── tests/                 # Suite de tests unitaires (Pytest)
│   ├── test_guardrails.py
│   └── test_memories.py
├── pyproject.toml         # Configuration du package et dépendances
└── README.md
\`\`\`

---

## Prérequis

- Python 3.10+
- Git
- [Ollama](https://ollama.com/) (pour faire tourner le modèle LLM en local)
- [Docker](https://www.docker.com/) (pour faire tourner l'instance Langfuse locale)

---

## Installation et Lancement

### 1. Cloner le dépôt

`bash
git clone <URL_DU_REPO>
cd atlas-ai-<votre-nom>
`

### 2. Environnement virtuel et dépendances

Il est fortement recommandé d'utiliser un environnement virtuel :


# Création et activation de l'environnement
python -m venv venv
source venv/bin/activate  # Sur Mac/Linux
# venv\Scripts\activate   # Sur Windows

# Installation du projet en mode éditable
`
pip install -e .
`

> 💡 **Pourquoi `pip install -e .` ?**
> Le `-e` signifie "éditable". Pip crée un lien vers le code source plutôt que de le copier. Toute modification dans le code est immédiatement prise en compte sans avoir à réinstaller le package. La configuration de l'installation est lue depuis le fichier `pyproject.toml`.

### 3. Démarrer l'infrastructure

**A. Lancer le modèle local (Ollama)**
S'assurer qu'Ollama tourne en arrière-plan, puis télécharger le modèle choisi :
`
ollama pull qwen3:4b-instruct-2507-q4_K_M
`

**B. Lancer le monitoring (Langfuse)**

# Dans un dossier séparé
git clone https://github.com/langfuse/langfuse
cd langfuse
docker compose up -d
`
N'oubliez pas de configurer vos variables d'environnement (`.env`) avec les clés API Langfuse locales.*

### 4. Utiliser l'assistant

Une fois installé, vous pouvez lancer l'assistant directement via la CLI :

\`\`\`bash
atlas-chat
# ou avec des paramètres spécifiques :
atlas-chat --model llama3.2:3b --url http://localhost:11434
\`\`\`

**Commandes spéciales en cours de chat :**
- `quit`, `exit` : Quitter l'assistant.
- `/forget <sujet>` : Demander à la base vectorielle d'oublier un souvenir précis.

---

## Tests Unitaires

La robustesse de l'application est assurée par une suite de tests unitaires (mocking des appels LLM, isolation de la DB vectorielle via des dossiers temporaires).

Pour lancer les tests :
`
pytest tests/
`

---

## L'équipe (Binôme)

*   **[Silva Costa José]** : Focus sur l'intégration du LLM (`llm.py`), la gestion de l'historique et des bases vectorielles (`memory.py`).
*   **[Lapeze Foucault]** : Focus sur la sécurité applicative (`guardrails.py`) et la remontée des métriques d'utilisation/évaluation (`monitoring.py`).
