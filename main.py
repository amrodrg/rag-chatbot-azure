import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from openai import AzureOpenAI
from typing import List, Optional

# Load environment variables
load_dotenv()

# Environment variables
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
API_VERSION = os.getenv("API_VERSION")

# Initialize Azure OpenAI client
# Adding Ocp-Apim-Subscription-Key header for Azure API Management (APIM) authentication
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    default_headers={"Ocp-Apim-Subscription-Key": AZURE_OPENAI_API_KEY}
)

app = FastAPI()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    question: str
    history: Optional[List[Message]] = None
    language: Optional[str] = "en"

class ChatResponse(BaseModel):
    answer: str

class EmbedRequest(BaseModel):
    text: str

class EmbedResponse(BaseModel):
    embedding: List[float]
    dimensions: int

def create_embedding(text: str) -> List[float]:
    response = client.embeddings.create(
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        input=text
    )
    return response.data[0].embedding

@app.get("/")
def rag_root():
    return {"message": "Hello from your RAG backend!"}

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):

    if not req.question.strip():
        return ChatResponse(answer="Error: Your question is empty.")
    
    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_CHAT_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You answer user questions."},
                {"role": "user", "content": req.question}
            ],
        )

        print(response.choices[0])

        ai_answer = response.choices[0].message.content
        return ChatResponse(answer=ai_answer)

    except Exception as e:
        return ChatResponse(answer=f"Error calling Azure OpenAI: {str(e)}")
    

@app.post("/embed", response_model=EmbedResponse)
def embed(req: EmbedRequest):
    if not req.text.strip():
        return EmbedResponse(embedding=[], dimensions=0)
    
    try:
        vec = create_embedding(req.text)
        return EmbedResponse(embedding=vec, dimensions=len(vec))
    except Exception as e:
        return EmbedResponse(embedding=[], dimensions=0)