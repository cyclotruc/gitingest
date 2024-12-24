import os
import numpy as np
import pytest
from gitingest.embedding import EmbeddingHandler

@pytest.fixture
def embedding_handler():
    return EmbeddingHandler()

def test_get_embeddings(embedding_handler):
    texts = ["Hello world", "Test sentence"]
    embeddings = embedding_handler.get_embeddings(texts)
    assert embeddings.shape[0] == 2
    assert embeddings.shape[1] > 0

def test_save_and_load_embeddings(embedding_handler, tmp_path):
    texts = ["Hello world", "Test sentence"]
    embeddings = embedding_handler.get_embeddings(texts)
    file_path = os.path.join(tmp_path, "embeddings.npy")
    embedding_handler.save_embeddings(embeddings, file_path)
    loaded_embeddings = embedding_handler.load_embeddings(file_path)
    assert np.array_equal(embeddings, loaded_embeddings)

def test_vectorize_repository(embedding_handler, tmp_path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    file1 = repo_path / "file1.txt"
    file1.write_text("Hello world")
    file2 = repo_path / "file2.txt"
    file2.write_text("Test sentence")
    embeddings = embedding_handler.vectorize_repository(str(repo_path))
    assert embeddings.shape[0] == 2
    assert embeddings.shape[1] > 0
