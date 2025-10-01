from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from bot import SportsBot

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Sports Committee Chatbot API", 
    version="1.0.0",
    description="AI-powered sports committee assistant API"
)

# Get allowed origins from environment variable
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,https://sports-spit-chatbot.vercel.app")
origins_list = [origin.strip() for origin in allowed_origins.split(",") if origin.strip()]

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize the bot
bot = None

@app.on_event("startup")
async def startup_event():
    global bot
    try:
        # Try to use processed_chunks.txt first, fallback to context.txt
        context_file = "processed_chunks.txt" if os.path.exists("processed_chunks.txt") else "context.txt"
        bot = SportsBot(context_file)
        print(f"✅ Sports bot initialized with {context_file}")
    except Exception as e:
        print(f"❌ Error initializing bot: {e}")
        raise

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.get("/")
async def root():
    return {"message": "Sports Committee Chatbot API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "bot_ready": bot is not None}

@app.post("/keep-alive")
async def keep_alive():
    """Keep-alive endpoint for preventing server sleep on Render"""
    if not bot:
        raise HTTPException(status_code=500, detail="Bot not initialized")
    
    # Check if bot has required API key (Gemini API)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="API key not found. Please set GEMINI_API_KEY environment variable."
        )
    
    try:
        # Send a simple keep-alive query
        response_text = bot.get_response("what is agility")
        return {"status": "alive", "timestamp": os.environ.get("TZ", "UTC")}
    except Exception as e:
        print(f"Error in keep-alive endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Keep-alive failed: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not bot:
        raise HTTPException(status_code=500, detail="Bot not initialized")
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Check if bot has required API key (Gemini API)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="API key not found. Please set GEMINI_API_KEY environment variable."
        )
    
    try:
        response_text = bot.get_response(request.message)
        return ChatResponse(response=response_text)
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    # Get server configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))  # Render uses PORT env var
    reload = os.getenv("RELOAD", "false").lower() == "true"  # Disable reload in production
    
    print(f"🚀 Starting FastAPI server on {host}:{port}")
    print(f"📖 API Documentation: http://{host}:{port}/docs")
    print(f"🔄 Auto-reload: {reload}")
    print(f"🌐 Allowed origins: {origins_list}")
    
    uvicorn.run(app, host=host, port=port, reload=reload)
