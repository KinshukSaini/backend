import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Use relative imports since we're in the app package
from .services.chatbot import Chatbot
from .services.retriever import Retriever
from .services.session_manager import SessionManager
from .routes.chat import router

# Load environment variables and initialize chatbot
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
retriever = Retriever()
chatbot = Chatbot(api_key=api_key, retriever=retriever)
session_manager = SessionManager()  # Add this line

# Create FastAPI app
app = FastAPI(title="Zanger AI API")

# Add CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://lexley.vercel.app", "http://localhost:3000", "http://localhost:5173", "https://app.lexley.co.uk"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store services in app state for routes to access
@app.on_event("startup")
async def startup_event():
    app.state.chatbot = chatbot
    app.state.session_manager = session_manager  # Add this line

# Include the chat router WITH /api prefix
app.include_router(router, prefix="/api")  # ✅ Added prefix="/api"

@app.get("/")
async def root():
    return {"message": "ZangerAI Legal Assistant API"}

@app.get("/health") 
async def health():
    return {"status": "healthy", "service": "ZangerAI"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("port", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
