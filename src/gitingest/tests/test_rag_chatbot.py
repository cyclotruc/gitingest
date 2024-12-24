import pytest
from gitingest.rag_chatbot import RAGChatbot

@pytest.fixture
def chatbot():
    return RAGChatbot(openai_api_key="your_openai_api_key", vector_db_path="path_to_vector_db")

def test_generate_response(chatbot):
    query = "What is the purpose of this repository?"
    response = chatbot.generate_response(query)
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_update_vector_store(chatbot):
    texts = ["This is a test document.", "Another test document."]
    chatbot.update_vector_store(texts)
    assert chatbot.vector_store is not None
    assert len(chatbot.vector_store) > 0

def test_load_vector_store(chatbot):
    vector_store = chatbot.load_vector_store()
    assert vector_store is not None
    assert len(vector_store) > 0

def test_save_vector_store(chatbot):
    chatbot.save_vector_store()
    assert chatbot.vector_db_path.exists()
