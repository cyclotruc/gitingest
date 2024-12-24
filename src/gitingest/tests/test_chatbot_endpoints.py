import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def mock_generate_response(monkeypatch):
    def mock_response(self, query):
        return "Mock response"
    monkeypatch.setattr("gitingest.rag_chatbot.RAGChatbot.generate_response", mock_response)

def test_query_chatbot(mock_generate_response):
    response = client.post("/chatbot/query", json={"query": "Test query"})
    assert response.status_code == 200
    assert response.json() == {"response": "Mock response"}

def test_query_chatbot_error(mock_generate_response, monkeypatch):
    def mock_response_error(self, query):
        raise Exception("Mock error")
    monkeypatch.setattr("gitingest.rag_chatbot.RAGChatbot.generate_response", mock_response_error)

    response = client.post("/chatbot/query", json={"query": "Test query"})
    assert response.status_code == 500
    assert response.json() == {"detail": "Mock error"}
