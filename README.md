# ATLAS Consulting — Assistant IA On-Premise

## Objectif du projet

Ce projet consiste à développer un prototype d'assistant IA **100% local** pour les collaborateurs du cabinet ATLAS Consulting.

En raison d'exigences de confidentialité strictes (clients santé et bancaires), ce projet n'utilise **aucune API Cloud** (ni OpenAI, ni Anthropic, etc.). L'objectif est de fournir un outil interne capable de :

- Répondre aux questions techniques des consultants de manière fluide (Streaming).
- Mémoriser le contexte des conversations à court et long terme (RAG).
- Filtrer les données sensibles pour éviter toute fuite via des règles de sécurité strictes (Guardrails).
- Monitorer l'utilisation et évaluer la qualité des réponses de l'assistant (Langfuse + LLM-as-a-Judge).

---

## Architecture et Fonctionnalités

Le projet est découpé en plusieurs briques métiers indépendantes :

1. **Moteur LLM (`llm.py`)** : Client local communiquant avec l'API REST d'Ollama. Supporte le streaming des réponses et la remontée des tokens consommés.
2. **Mémoire Intelligente (`memory.py`)** :
   - _Court terme_ : Conserve le contexte de la session active et génère un résumé automatique tous les N tours.
   - _Long terme_ : Base de données vectorielle (ChromaDB) avec recherche sémantique, filtrage par tags métier, et capacité d'oubli spécifique (commande `/forget`).
3. **Sécurité et Gouvernance (`guardrails.py`)** : Pipeline de validation des requêtes (longueur, blocage de sujets stricts, protection contre les prompt injections, masquage des données personnelles PII) et validation sémantique par un LLM Juge.
4. **Observabilité (`monitoring.py` & Langfuse)** : Traces hiérarchiques de chaque interaction, calcul des coûts/tokens, et notation automatique de la pertinence des réponses (LLM-as-a-judge).

---

## Architecture & Décisions Techniques (ADR)

### Gestion du Modèle (Niveau 2)

Nous avons choisi de créer un modèle dérivé nommé `atlas` via un **Modelfile** Ollama.

- **Choix du modèle de base** : `llama3.2:3b` pour son rapport performance/légèreté.
- **Emplacement du System Prompt** : La définition de la Persona vit dans le Modelfile. Cela garantit que le modèle possède une identité constante, quel que soit le client utilisé. Cependant, les instructions contextuelles (RAG) restent gérées par le code applicatif pour permettre une injection dynamique.
- **Priorité des configurations** : La configuration externe (`atlas.yaml`) prévaut sur les paramètres du Modelfile. Lors de l'appel API, les options envoyées écrasent les PARAMETERS du modèle, offrant ainsi une flexibilité de test sans nécessiter de recompilation du modèle.
- **Interface** : La CLI pointe par défaut vers le modèle `atlas`. Cela simplifie l'expérience utilisateur et permet à l'équipe technique de changer le modèle de base (`FROM`) dans le futur sans impacter les scripts des utilisateurs.

---

## Structure du projet

atlas-ai/
├── atlas/                # Code source principal (Package Python)
│   ├── __init__.py
│   ├── cli.py            # Point d'entrée et orchestration
│   ├── guardrails.py     # Règles de sécurité et filtrage
│   ├── llm.py            # Client API Ollama
│   ├── memory.py         # Gestion ChromaDB et historique
│   └── monitoring.py     # LLM Judge pour l'évaluation
├── config/               # Fichiers de configuration
├── data/
│   └── memory/           # Base de données vectorielle locale (ChromaDB)
├── scripts/              # Scripts utilitaires
├── tests/                # Suite de tests unitaires (Pytest)
│   ├── test_guardrails.py
│   └── test_memories.py
├── pyproject.toml        # Configuration du package et dépendances
└── README.md

---

## Prérequis

- Python 3.10+
- Git
- [Ollama](https://ollama.com/) (pour faire tourner le modèle LLM en local)
- [Docker](https://www.docker.com/) (pour faire tourner l'instance Langfuse locale)

---

## Installation et Lancement

### 1. Cloner le dépôt

\`\`\`bash
git clone <URL_DU_REPO>
cd atlas-ai-<votre-nom>
\`\`\`

### 2. Environnement virtuel et dépendances

Il est fortement recommandé d'utiliser un environnement virtuel :

\`\`\`bash

# Création et activation de l'environnement

python -m venv venv
source venv/bin/activate # Sur Mac/Linux

# venv\Scripts\activate # Sur Windows

# Installation du projet en mode éditable

pip install -e .
\`\`\`

> 💡 **Pourquoi `pip install -e .` ?**
> Le `-e` signifie "éditable". Pip crée un lien vers le code source plutôt que de le copier. Toute modification dans le code est immédiatement prise en compte sans avoir à réinstaller le package. La configuration de l'installation est lue depuis le fichier `pyproject.toml`.

### 3. Démarrer l'infrastructure

**A. Lancer le modèle local (Ollama)**
S'assurer qu'Ollama tourne en arrière-plan, puis télécharger le modèle choisi :
\`\`\`bash
ollama pull llama3.2:3b

# Compiler le modèle custom Atlas à partir du Modelfile

ollama create atlas -f Modelfile
\`\`\`

**B. Lancer le monitoring (Langfuse)**
\`\`\`bash

# Dans un dossier séparé

git clone https://github.com/langfuse/langfuse
cd langfuse
docker compose up -d
\`\`\`
_N'oubliez pas de configurer vos variables d'environnement (`.env`) avec les clés API Langfuse locales._

### 4. Utiliser l'assistant

Une fois installé, vous pouvez lancer l'assistant directement via la CLI :

\`\`\`bash
atlas-chat

# ou avec des paramètres spécifiques :

atlas-chat --model atlas --url http://localhost:11434
\`\`\`

**Commandes spéciales en cours de chat :**

- `quit`, `exit` : Quitter l'assistant.
- `/forget <sujet>` : Demander à la base vectorielle d'oublier un souvenir précis.

---

## Tests Unitaires

La robustesse de l'application est assurée par une suite de tests unitaires (mocking des appels LLM, isolation de la DB vectorielle via des dossiers temporaires).

Pour lancer les tests :
\`\`\`bash
pytest tests/
\`\`\`

---

## L'équipe (Binôme)

*   **[Silva Costa José]** : Focus sur l'intégration du LLM (`llm.py`), la gestion de l'historique et des bases vectorielles (`memory.py`).
*   **[Lapeze Foucault]** : Focus sur la sécurité applicative (`guardrails.py`) et la remontée des métriques d'utilisation/évaluation (`monitoring.py`).
