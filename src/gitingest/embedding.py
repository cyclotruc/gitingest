from sentence_transformers import SentenceTransformer
import numpy as np
import os

class EmbeddingHandler:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)

    def get_embeddings(self, texts):
        return self.model.encode(texts, convert_to_tensor=True)

    def save_embeddings(self, embeddings, file_path):
        np.save(file_path, embeddings)

    def load_embeddings(self, file_path):
        return np.load(file_path)

    def vectorize_repository(self, repo_path):
        file_contents = []
        for root, _, files in os.walk(repo_path):
            for file in files:
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_contents.append(f.read())
        return self.get_embeddings(file_contents)
