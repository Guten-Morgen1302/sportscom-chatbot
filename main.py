from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from pathlib import Path
from dotenv import load_dotenv
from bot import SportsBot

load_dotenv()

app = FastAPI(
    title="Sports Committee Chatbot API", 
    version="1.0.0",
    description="AI-powered sports committee assistant API"
)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins == "*":
    origins_list = ["*"]
else:
    origins_list = [origin.strip() for origin in allowed_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bot = None

@app.on_event("startup")
async def startup_event():
    global bot
    try:
        context_file = "context.txt"
        bot = SportsBot(context_file)
        print(f"✅ Sports bot initialized with {context_file}")
    except Exception as e:
        print(f"❌ Error initializing bot: {e}")
        raise

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.get("/")
async def serve_frontend():
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return Response(
            content=html_content,
            media_type="text/html",
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
    return {"message": "Sports Committee Chatbot API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "bot_ready": bot is not None}

@app.post("/keep-alive")
async def keep_alive():
    if not bot:
        raise HTTPException(status_code=500, detail="Bot not initialized")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="API key not found. Please set GEMINI_API_KEY environment variable."
        )
    
    try:
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
        error_msg = str(e)
        print(f"Error in chat endpoint: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Gemini API Error: {error_msg}")

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    print(f"🚀 Starting FastAPI server on {host}:{port}")
    print(f"📖 API Documentation: http://{host}:{port}/docs")
    print(f"🔄 Auto-reload: {reload}")
    print(f"🌐 Allowed origins: {origins_list}")
    
    uvicorn.run(app, host=host, port=port, reload=reload)
