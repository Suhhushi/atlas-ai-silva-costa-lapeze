import pytest
from atlas.memory import VectorMemory, ConversationMemory

# Mock LLM
class MockLLMClient:
    """Faux client LLM pour tester la génération de résumé sans appel réseau."""
    def __init__(self, expected_summary="Voici le résumé de la conversation."):
        self.expected_summary = expected_summary

    def chat_stream(self, messages):
        yield self.expected_summary

@pytest.fixture
def vector_db(tmp_path):
    """
    Fixture : Crée une instance VectorMemory isolée pour chaque test.
    tmp_path est fourni par pytest et crée un dossier temporaire unique.
    """
    return VectorMemory(persist_directory=str(tmp_path))

def test_save_and_search_memories(vector_db):
    """Teste la sauvegarde et la récupération basique d'un souvenir."""
    vector_db.save_interaction("Quel est mon projet ?", "Tu travailles sur ATLAS.")
    
    # On cherche une phrase sémantiquement très proche
    results = vector_db.search_memories("Sur quel projet je travaille ?")
    
    assert len(results) > 0
    assert "Question: Quel est mon projet ?" in results[0]
    assert "Réponse: Tu travailles sur ATLAS." in results[0]

def test_search_with_metadata_filter(vector_db):
    """Teste le filtrage des souvenirs par tag métier."""
    vector_db.save_interaction("Budget Q3", "10k euros", metadata={"topic": "finance"})
    vector_db.save_interaction("Client X", "Rendez-vous mardi", metadata={"topic": "commercial"})
    
    # filtre uniquement sur le commercial
    results = vector_db.search_memories("client", filter_metadata={"topic": "commercial"})
    
    assert len(results) == 1
    assert "Client X" in results[0]
    assert "Budget" not in results[0]

def test_forget_memory(vector_db):
    """Teste la fonctionnalité d'oubli d'un souvenir spécifique."""
    vector_db.save_interaction("Secret d'entreprise", "Le code de la porte est 1234.")
    
    # Vérifie que le souvenir est bien là
    assert len(vector_db.search_memories("code de la porte")) > 0
    
    # demande de l'oublier
    success = vector_db.forget("code de la porte")
    assert success is True
    
    # On vérifie qu'il n'existe plus
    assert len(vector_db.search_memories("code de la porte")) == 0

def test_empty_memory_search(vector_db):
    """Teste la recherche dans une base vide ne plante pas."""
    results = vector_db.search_memories("Test")
    assert results == []

@pytest.fixture
def conv_memory():
    """Fixture : Crée une mémoire courte configurée pour résumer tous les 3 tours."""
    return ConversationMemory(summarize_every_n=3)

def test_add_message_and_history(conv_memory):
    """Teste l'ajout de messages et l'incrémentation du compteur de tours."""
    conv_memory.add_message("user", "Bonjour")
    conv_memory.add_message("assistant", "Salut !")
    
    history = conv_memory.get_history()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert conv_memory.turn_count == 1 # Seuls les messages "user" comptent comme un tour

def test_build_prompt_with_context(conv_memory):
    """Teste la construction du prompt enrichi avec la mémoire long terme."""
    question = "Qui suis-je ?"
    souvenirs = ["Question: Comment je m'appelle ?\nRéponse: Tu es Jean."]
    
    prompt = conv_memory.build_prompt_with_context(question, souvenirs)
    
    assert "Tu es Jean" in prompt
    assert "Nouvelle question : Qui suis-je ?" in prompt

def test_build_prompt_without_context(conv_memory):
    """Teste le prompt quand il n'y a pas de souvenirs passés."""
    question = "Que fait 2+2 ?"
    prompt = conv_memory.build_prompt_with_context(question, [])
    
    # Si pas de contexte doit juste renvoyer la question pure
    assert prompt == "Que fait 2+2 ?"

def test_needs_summary(conv_memory):
    """Teste la détection du moment opportun pour résumer la session."""
    assert conv_memory.needs_summary() is False
    
    # simule 3 tours de conversation
    conv_memory.add_message("user", "Q1")
    conv_memory.add_message("user", "Q2")
    assert conv_memory.needs_summary() is False
    
    conv_memory.add_message("user", "Q3")
    assert conv_memory.needs_summary() is True

def test_generate_summary_resets_memory(conv_memory):
    """Teste que la génération du résumé purge bien la mémoire courte."""
    # remplit la mémoire
    conv_memory.add_message("user", "Je veux parler de Python.")
    conv_memory.add_message("assistant", "D'accord, que veux-tu savoir ?")
    
    # injecte le faux LLM
    mock_llm = MockLLMClient("L'utilisateur veut apprendre Python.")
    
    summary = conv_memory.generate_summary(mock_llm)
    
    assert summary == "L'utilisateur veut apprendre Python."
    assert len(conv_memory.messages) == 0 
    assert conv_memory.turn_count == 0 