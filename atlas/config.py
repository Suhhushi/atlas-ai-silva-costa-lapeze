import yaml
from pydantic import BaseModel, Field, ValidationError
from typing import List

class ModelConfig(BaseModel):
    name: str
    temperature: float = Field(default=0.3, ge=0.0, le=1.0, description="Créativité du modèle")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    num_ctx: int = Field(default=4096, gt=0, description="Taille de la fenêtre de contexte")

class PersonaConfig(BaseModel):
    name: str
    system_prompt: str

class MemoryConfig(BaseModel):
    top_k: int = Field(default=5, gt=0)
    min_similarity: float = Field(default=0.7, ge=0.0, le=1.0)

class GuardrailsConfig(BaseModel):
    enabled: bool = True
    blocked_topics: List[str] = Field(default_factory=list)

class AtlasConfig(BaseModel):
    model: ModelConfig
    persona: PersonaConfig
    memory: MemoryConfig
    guardrails: GuardrailsConfig

def load_config(filepath: str = "config/atlas.yaml") -> AtlasConfig:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        return AtlasConfig(**data)
        
    except FileNotFoundError:
        raise RuntimeError(f" Erreur : Le fichier de configuration '{filepath}' est introuvable.")
    except yaml.YAMLError as e:
        raise RuntimeError(f" Erreur de syntaxe YAML : {e}")
    except ValidationError as e:
        # Formatage
        print("\n ERREUR DE CONFIGURATION ")
        for error in e.errors():
            chemin = " -> ".join([str(loc) for loc in error['loc']])
            print(f"  - Champ : [{chemin}]")
            print(f"    Problème : {error['msg']}")
        raise SystemExit(1)