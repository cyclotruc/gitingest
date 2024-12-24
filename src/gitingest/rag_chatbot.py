import os
import openai
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts import PromptTemplate

class RAGChatbot:
    def __init__(self, openai_api_key, vector_db_path):
        self.openai_api_key = openai_api_key
        openai.api_key = self.openai_api_key
        self.vector_db_path = vector_db_path
        self.vector_store = self.load_vector_store()

    def load_vector_store(self):
        if os.path.exists(self.vector_db_path):
            return FAISS.load_local(self.vector_db_path, OpenAIEmbeddings())
        else:
            raise FileNotFoundError(f"Vector database not found at {self.vector_db_path}")

    def save_vector_store(self):
        self.vector_store.save_local(self.vector_db_path)

    def update_vector_store(self, texts):
        embeddings = OpenAIEmbeddings()
        new_vectors = embeddings.embed_documents(texts)
        self.vector_store.add_documents(new_vectors)
        self.save_vector_store()

    def generate_response(self, query):
        retriever = self.vector_store.as_retriever()
        qa_chain = RetrievalQA(
            retriever=retriever,
            llm=OpenAI(api_key=self.openai_api_key),
            prompt_template=PromptTemplate(
                input_variables=["context", "question"],
                template="Context: {context}\n\nQuestion: {question}\n\nAnswer:"
            )
        )
        return qa_chain.run(query)
