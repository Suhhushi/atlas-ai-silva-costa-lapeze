# 🏢 TP — Projet ATLAS : Déploiement d'un assistant IA local

**Durée** : 1 journée
**Format** : binômes
**Prérequis** : laptop (8 Go RAM min.), Python 3.10+, Git, Docker recommandé, éventuellement Google Colab (compte Google requis)

---

## 🎯 Contexte — Le brief client

> **ATLAS Consulting** est un cabinet de conseil IT de 50 personnes. Pour des raisons de confidentialité contractuelle (clients bancaires et santé), la direction **refuse catégoriquement** d'envoyer les données clients à OpenAI, Anthropic ou Mistral Cloud.
>
> Elle vous mandate en tant que **tech lead** pour livrer, en une journée, un **prototype d'assistant IA 100 % on-premise** qui servira aux consultants pour :
> - répondre à des questions techniques
> - mémoriser les échanges précédents
> - respecter des règles métier (pas d'info client leakée, pas de secrets en clair)
>
> La direction veut **un livrable concret** en fin de journée : code versionné, démo live, métriques d'usage. Pas de slides. Pas d'outil "tout prêt" type AnythingLLM : vous devez **comprendre et coder** chaque brique.

---

## 🚀 Sprint 0 — Kickoff

Votre binôme est l'équipe projet. Vous devez :

1. **Créer un repo Git** (GitHub, GitLab, Gitea local peu importe). Nom : `atlas-ai-<votre-nom>`.
2. **Définir l'arbo** du projet. Exemple à adapter :
   ```
   atlas/
   ├── atlas/           # package Python
   │   ├── __init__.py
   │   ├── llm.py       # wrapper Ollama
   │   ├── memory.py    # gestion mémoire
   │   ├── monitoring.py
   │   └── guardrails.py
   ├── scripts/
   ├── tests/
   ├── config/
   ├── data/
   ├── pyproject.toml   # ou requirements.txt
   └── README.md
   ```
3. **Rédiger un README minimal** : objectif du projet, comment lancer, qui fait quoi dans le binôme.
4. **Créer un environnement Python isolé** (`venv`, `uv`, `poetry`, au choix).

**Critère d'acceptation S0** : `git log` affiche au moins 2 commits (un par personne), le README explique comment lancer, `pip install -e .` (ou équivalent) fonctionne sans erreur.

---

## 🧱 Sprint 1 — Mettre le LLM en ligne

### Objectif
Un consultant doit pouvoir lancer `atlas-chat` dans son terminal, poser une question, et recevoir une réponse du modèle local.

### Tâches
1. **Installer Ollama** : https://ollama.com/download
2. **Télécharger un modèle** adapté à votre machine :
   - 8 Go RAM → `ollama pull llama3.2:3b` ou `ollama pull qwen3:4b`
   - 16 Go RAM → `ollama pull qwen3:8b` ou `ollama pull phi4-mini`
   - < 8 Go → `ollama pull gemma3:1b`
3. **Vérifier l'API** : `curl http://localhost:11434/api/tags` doit lister vos modèles.
4. **Coder un client Python** qui :
   - parle à l'API Ollama (`POST /api/chat`) sans passer par la lib `ollama-python` au début — **utilisez `requests` ou `httpx` pur** pour comprendre ce qui se passe
   - gère un historique de messages (multi-tours)
   - supporte le streaming de la réponse (bonus)
5. **Exposer une CLI** (`argparse`, `click`, `typer` au choix). Minimum : `atlas-chat` ouvre une boucle interactive.

### Contraintes
- **Pas de LangChain, pas de LlamaIndex** à ce stade. Vous écrivez le code vous-même.
- Le modèle utilisé doit être **paramétrable** (via CLI flag ou fichier de config).
- Timeout configurable sur les requêtes.

### Critère d'acceptation S1
Un consultant lance `atlas-chat`, pose trois questions dépendantes et les réponses sont cohérentes — le modèle a bien le contexte.

---

## 🧠 Sprint 2 — Donner une mémoire

### Objectif
Deux types de mémoire doivent coexister :
1. **Mémoire courte** (dans la session) : déjà acquise au sprint 1
2. **Mémoire longue** (persistante entre sessions) : le bot doit retrouver des éléments de conversations passées

### Tâches
1. **Comprendre la limite de la fenêtre de contexte** : lancez un dialogue de 50 tours. Qu'observe-t-on ? Mesurez les tokens envoyés à chaque tour (approximation : `len(text.split()) * 1.3`).
2. **Implémenter une mémoire vectorielle** avec **ChromaDB** :
   ```bash
   pip install chromadb
   ```
   ```python
   import chromadb
   client = chromadb.PersistentClient(path="./data/memory")
   collection = client.get_or_create_collection("conversations")
   ```
   > ℹ️ ChromaDB ≥ 1.x embarque un modèle d'embedding par défaut (`all-MiniLM-L6-v2`). Vous n'avez **pas besoin** d'installer `sentence-transformers` explicitement.

3. **Définir votre stratégie de mémorisation**. Questions à trancher en équipe :
   - Qu'est-ce qu'on stocke ? Chaque message ? Chaque paire Q/R ? Des résumés ?
   - Quand on cherche en mémoire ? À chaque tour ? Seulement sur certains mots-clés ?
   - Combien de souvenirs on injecte dans le prompt ? (Attention à la taille du contexte !)
   - Comment on gère les doublons / informations contradictoires ?

4. **Injecter les souvenirs pertinents dans le system prompt** au moment de la requête.

5. **Tester** : fermez votre CLI, rouvrez-la, demandez au bot "Qu'est-ce qu'on s'est dit hier sur le projet X ?". Il doit retrouver l'info.

### Bonus si vous avancez vite
- Ajouter un **résumé automatique** de la conversation tous les N tours (appel au LLM pour condenser l'historique → stocké comme "souvenir long terme")
- Ajouter un **tag métier** aux souvenirs (`{"client": "BNP", "topic": "planification"}`) pour filtrer les recherches
- Implémenter l'**oubli** : commande `/forget <query>` qui supprime les souvenirs matchant

### Critère d'acceptation S2
Scénario à dérouler devant le formateur :
1. Session A : "Je m'appelle Dupont et je travaille sur le projet Luna pour le client Atos."
2. Fermer la CLI.
3. Session B : "Sur quel projet je bosse ?" → réponse correcte attendue.

---

## 🔍 Sprint 3 — Observer & gouverner

### Objectif
Sans télémétrie, impossible d'améliorer. Sans guardrails, impossible d'aller en prod.

### Partie A — Monitoring

Vous devez produire un **log structuré** de chaque interaction. Deux voies sont acceptables — **la voie B (Langfuse) est fortement valorisée** car c'est ce que vous rencontrerez en entreprise.

#### 🛠️ Voie A — Monitoring maison (JSONL + pandas)

Concevez votre format de trace (JSONL recommandé).

**Champs minimum attendus** par ligne de log :
- `timestamp` ISO 8601
- `session_id`
- `model`
- `prompt_tokens` / `completion_tokens` (vrai compteur dans la réponse Ollama : champs `prompt_eval_count` et `eval_count`)
- `latency_ms`
- `user_message` (hashé ou tronqué selon votre politique RGPD — à vous de trancher)
- `assistant_message`
- `memory_hits` : nombre de souvenirs injectés

**Livrable technique** : un décorateur Python ou un context manager qui wrappe l'appel LLM et écrit la trace.

```python
# Squelette à étoffer
from functools import wraps
import time, json
from datetime import datetime, timezone

def traced(log_path: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            # ... à vous de compléter
            return result
        return wrapper
    return decorator
```

Puis **analysez** : écrivez `scripts/analyze_traces.py` qui sort latence médiane / p95, top requêtes les plus longues, distribution des tailles de prompt, et coût estimé si on avait utilisé GPT-4o à la place (à vous de chercher les prix actuels). Utilisez pandas + matplotlib (ou rich pour la CLI).

#### ⭐ Voie B — Langfuse self-hosted (fortement apprécié)

Langfuse est **le standard open-source** de l'observabilité LLM en entreprise : traces arborescentes, suivi des coûts, évaluations, gestion de prompts centralisée. L'instrumenter soi-même est un skill qui vaut de l'or sur un CV.

**Prérequis** : Docker + Docker Compose, 16 Go RAM recommandés (Langfuse v3 démarre Postgres, ClickHouse, Redis, MinIO, web, worker — ~6 containers, 3-4 Go de RAM additionnels).

1. **Démarrer la stack** :
   ```bash
   git clone https://github.com/langfuse/langfuse
   cd langfuse
   # Générer des secrets dans .env (NEXTAUTH_SECRET, SALT, ENCRYPTION_KEY)
   # openssl rand -base64 32  et  openssl rand -hex 32
   docker compose up -d
   ```
   Attendez que `langfuse-web-1` log `Ready` (2-3 min). Ouvrez http://localhost:3000, créez un compte, un projet, récupérez `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY`.

2. **Installer le SDK** :
   ```bash
   pip install langfuse
   ```

3. **Instrumenter votre code** — deux approches, vous choisissez :
   - **Décorateur `@observe()`** pour une instrumentation locale et fine :
     ```python
     from langfuse import observe, Langfuse

     langfuse = Langfuse()  # lit les env vars LANGFUSE_*

     @observe(name="atlas_chat")
     def chat(user_message: str, history: list) -> str:
         # votre code existant
         ...
     ```
   - **Intégration OpenTelemetry** si vous préférez la voie standardisée.

4. **Exercices d'analyse** dans l'UI Langfuse :
   - Retrouver les 5 traces les plus lentes
   - Identifier les sessions où la mémoire a été utilisée
   - Créer un **dashboard custom** avec latence p95 et tokens consommés par jour
   - Créer une **évaluation LLM-as-a-judge** qui note la qualité des réponses (bonus+)

**À documenter** (cela servira au Sprint 5) : captures d'écran de vos dashboards, schéma de la stack Langfuse, raisonnement sur pourquoi / pourquoi pas choisir Langfuse en prod.

> 💡 Si Langfuse rame trop sur votre laptop : passez en Voie A pour finir le sprint, puis **revenez sur Langfuse** en fin de journée si le temps le permet. Mieux vaut un monitoring maison qui marche qu'un Langfuse planté.

### Partie B — Gouvernance / Guardrails

Écrivez un module `guardrails.py` qui applique au moins **4 règles** parmi :

1. **Detection de PII** (numéros de carte, emails, IBAN, numéro de sécu) en entrée → log + masquage avant envoi au LLM
2. **Blocage de sujets interdits** (liste configurable en YAML)
3. **Limitation de longueur** (requête > N mots → refus)
4. **Detection de prompt injection** (patterns type "ignore previous instructions", "tu es maintenant", "<|system|>")
5. **Rate limiting** local (max N requêtes / minute par session)
6. **Validation de la sortie** : le LLM ne doit pas reproduire les PII qu'on a masqués en entrée

Chaque règle doit :
- être **testable unitairement** (écrivez les tests dans `tests/test_guardrails.py`)
- logger son déclenchement dans les traces
- être **activable/désactivable** via configuration

### Critère d'acceptation S3
- Chaque interaction produit une trace (JSONL maison OU visible dans Langfuse)
- Au moins 3 métriques agrégées sont produites (script d'analyse OU dashboard Langfuse)
- Un prompt contenant un faux numéro de CB (ex : `4532015112830366`) déclenche le guardrail et le masque avant envoi au modèle
- Au moins 3 tests unitaires passent (`pytest`)
- Les binômes ayant choisi Langfuse ont capturé au moins une trace hiérarchique (chat → récupération mémoire → appel LLM)

---

## 🎨 Sprint 4 — Configurer & personnaliser

### Objectif
Votre assistant doit avoir une **personnalité cohérente** et un comportement paramétrable sans modifier le code.

### Niveau 1 — Configuration externe

1. Créer `config/atlas.yaml` :
   ```yaml
   model:
     name: "llama3.2:3b"
     temperature: 0.3
     top_p: 0.9
     num_ctx: 4096

   persona:
     name: "Atlas"
     system_prompt: |
       Tu es Atlas, assistant IA interne d'ATLAS Consulting.
       Tu réponds en français de façon concise et précise.
       Tu refuses poliment toute requête hors du périmètre professionnel.

   memory:
     top_k: 5
     min_similarity: 0.7

   guardrails:
     enabled: true
     blocked_topics: ["politique", "religion"]
   ```
2. Charger la config via `pyyaml` ou `pydantic-settings`.
3. Valider avec un schema Pydantic — erreurs claires si la config est invalide.

### Niveau 2 — Modelfile Ollama

Créez un **vrai modèle dérivé** dans Ollama :

```dockerfile
# Modelfile
FROM llama3.2:3b

SYSTEM """
Tu es Atlas, assistant IA d'ATLAS Consulting. (...)
"""

PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
PARAMETER stop "Human:"
PARAMETER stop "User:"
```

```bash
ollama create atlas -f Modelfile
ollama run atlas  # test interactif
```

**Questions à trancher** dans votre équipe :
- Le system prompt doit-il vivre dans le Modelfile ou dans le code applicatif ? Pourquoi ?
- Quel impact si un utilisateur change la config YAML mais pas le Modelfile ?
- Votre CLI doit-elle pointer vers `atlas` ou vers `llama3.2:3b` + system prompt côté code ?

**Documentez votre choix** dans un fichier `docs/architecture.md` (section "Decisions").

### Niveau 3 — BONUS : Fine-tuning LoRA sur Colab

**⚠️ Bonus réservé aux binômes qui ont terminé les niveaux 1 et 2.**

L'objectif : fine-tuner `llama-3.2-3b` sur un petit dataset métier ATLAS (50-100 exemples Q/R sur un domaine imaginaire de votre choix : ex. "expert en normes IFRS", "assistant interne RH", etc.).

1. **Préparer le dataset** : `data/finetune.jsonl` au format :
   ```json
   {"instruction": "Quelle est la norme IFRS pour...", "input": "", "output": "..."}
   ```
   Générez-le si besoin avec le LLM lui-même (meta !).

2. **Ouvrir un Colab** avec GPU T4 (Runtime → Change runtime type → T4).
3. **Utiliser le notebook officiel Unsloth** pour Llama 3.2 3B : https://docs.unsloth.ai (cherchez "Llama 3.2 Colab notebook").
4. **Entraîner** (15-30 min sur T4 pour 3 époques sur 100 exemples).
5. **Exporter en GGUF** : Unsloth le fait en une cellule (`model.save_pretrained_gguf(...)`).
6. **Télécharger le `.gguf`** et l'importer dans Ollama via un Modelfile :
   ```dockerfile
   FROM ./atlas-tuned.gguf
   SYSTEM "..."
   ```
   ```bash
   ollama create atlas-tuned -f Modelfile
   ```

**Pièges connus** :
- Le runtime Colab gratuit meurt après ~12h ou 40 min d'inactivité
- Le merge LoRA → full model peut OOM sur la RAM Colab (12.7 Go) : mergez en local si possible
- Les modèles "gated" (Llama, Gemma) requièrent un token HuggingFace et l'acceptation de la licence

### Critère d'acceptation S4
- `atlas-chat` charge la config YAML, et changer la température la dans YAML modifie le comportement **sans toucher au code**
- `ollama list` montre votre modèle custom `atlas`
- Vous avez documenté vos décisions d'architecture dans `docs/architecture.md`
- (Bonus) Un GGUF fine-tuné tourne localement

---

## 📖 Sprint 5 — Documentation projet

### Objectif
Produire un **dossier `docs/` réutilisable** qui permettrait à un autre développeur (ou à un client) de reprendre votre travail sans vous. En entreprise, c'est ça le livrable final.

La qualité attendue : **"je peux l'envoyer à un décideur technique sans rougir"**.

### Exemple d'organisation (à adapter)

Rien n'est imposé, mais voici une structure de référence qui a fait ses preuves :

```
docs/
├── README.md              # Vue d'ensemble + table des matières
├── architecture.md        # Diagramme + composants + flux de données
├── installation.md        # Guide pas-à-pas reproductible
├── configuration.md       # Options exposées
├── monitoring.md          # Observabilité, traces, métriques
├── governance.md          # Guardrails, RGPD, rétention des logs
├── operations.md          # Runbook : démarrer, arrêter, purger, rollback
├── security.md            # Modèle de menaces + décisions
└── adr/                   # Architecture Decision Records
    └── 001-choix-ollama.md
```

**ADR** (Architecture Decision Record) : format court qui trace vos décisions structurantes. Cherchez le format standard si vous ne connaissez pas — c'est une compétence attendue en entreprise.

À vous de choisir le niveau de détail, les outils (Mermaid, Excalidraw, mkdocs…), le découpage. La seule vraie contrainte : **que ce soit utilisable par quelqu'un d'extérieur au projet**.

### Critère d'acceptation S5 — Test de l'impostor

Vous échangez votre `docs/` avec un autre binôme. **Sans poser de question**, l'autre équipe doit pouvoir :
1. Comprendre ce que fait le projet et son architecture
2. Refaire tourner le projet sur sa machine, guidée uniquement par votre doc
3. Répondre à : *"quelle est la politique RGPD sur les logs ?"* et *"pourquoi Ollama ?"*

Si l'un de ces points échoue, la doc est à retravailler.

### Livrable final

Repo Git avec `docs/` committé, tag `v1.0`, lien envoyé au formateur.

---

## 📊 Grille d'évaluation

| Critère | Poids |
|---|---|
| S1 — CLI fonctionnelle avec historique | 10 % |
| S2 — Mémoire vectorielle persistante | 10 % |
| S3 — Monitoring structuré + analyse | 10 % |
| S3 — Guardrails avec tests | 10 % |
| S4 — Config externe + Modelfile | 10 % |
| **S5 — Documentation projet complète** | **20 %** |
| Qualité du code (structure, lisibilité, tests) | 15 % |
| Qualité du Git (commits atomiques, messages clairs) | 5 % |
| Test de l'impostor (doc croisée réussie) | 10 % |
| **Bonus — Langfuse self-hosted instrumenté** | **+10 %** |
| Bonus — Fine-tuning LoRA réussi | +10 % |
| Bonus — Résumé auto / oubli / multi-modèles | +5 % |

---

## 🆘 Antisèche rapide (en cas de galère)

### Ollama ne démarre pas
- Linux/Mac : `ollama serve` manuellement dans un terminal dédié
- Windows : relancer l'app Ollama depuis le menu
- Port 11434 occupé : `lsof -i :11434` puis `kill`

### Le modèle est trop lent
- Essayez un plus petit : `gemma3:1b` (274 Mo) ou `llama3.2:1b`
- Réduisez `num_ctx` dans les params (2048 au lieu de 4096)
- Fermez Chrome/Slack/Teams qui bouffent la RAM

### ChromaDB : "sqlite3 version too old"
- Python ≥ 3.11 requis, ou installez une version antérieure de chromadb

### Ollama sur Colab (secours si laptop KO)
Colab peut faire tourner Ollama via ngrok — mais c'est hors sujet du TP. Si vraiment tout est cassé, utilisez l'API Groq (gratuite, compatible OpenAI, modèles open source) pour continuer le sprint en attendant.

---

## 📚 Ressources (à consulter **en autonomie**)

- Ollama API : https://github.com/ollama/ollama/blob/main/docs/api.md
- ChromaDB : https://docs.trychroma.com
- Ollama Modelfile : https://github.com/ollama/ollama/blob/main/docs/modelfile.md
- Unsloth (fine-tuning) : https://docs.unsloth.ai
- Langfuse (bonus monitoring) : https://langfuse.com/self-hosting

> 🚫 **Interdit** : tutoriels "build a local AI in 10 min with AnythingLLM / Open WebUI / LM Studio". Vous êtes des développeurs, pas des utilisateurs finaux.

---

**Bon dev. Le code de votre binôme ira sur GitHub. Rendez-le présentable.** 🚀
