from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from gitingest.rag_chatbot import RAGChatbot

router = APIRouter()

class ChatbotRequest(BaseModel):
    query: str

class ChatbotResponse(BaseModel):
    response: str

# Initialize the RAGChatbot with your OpenAI API key and vector database path
chatbot = RAGChatbot(openai_api_key="your_openai_api_key", vector_db_path="path_to_vector_db")

@router.post("/chatbot/query", response_model=ChatbotResponse)
async def query_chatbot(request: ChatbotRequest):
    try:
        response = chatbot.generate_response(request.query)
        return ChatbotResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
