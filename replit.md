# SPIT SportsCom Chatbot

## Project Overview
An AI-powered chatbot designed for SPIT SportsCom committee to help students with sports-related queries. The bot responds in Hinglish and provides information about:
- Agility Cup events and team formation
- Spoorthi sports fest details
- Committee selections and interviews
- Sports trials and venues
- General sports events and schedules

## Current Status
✅ **FastAPI Backend Successfully Migrated** - Ready for production
- Python 3.11 environment with FastAPI backend
- Backend running on port 5000 with 0.0.0.0 binding
- Dark theme frontend with red accents
- Google Gemini AI integration with improved context handling
- All endpoints tested and working perfectly

## Recent Changes (October 01, 2025)
- ✅ **Successfully imported from GitHub and configured for Replit**
- ✅ Installed Python 3.11 environment
- ✅ Installed all required dependencies (FastAPI, Uvicorn, google-genai, etc.)
- ✅ Cleaned up requirements.txt (removed duplicates)
- ✅ Configured GEMINI_API_KEY secret in Replit
- ✅ Configured workflow to run FastAPI server on port 5000 with 0.0.0.0 binding
- ✅ Updated CORS settings to allow all origins for Replit proxy compatibility
- ✅ Tested all endpoints: /health, /chat - all working perfectly with Gemini AI
- ✅ Verified frontend displays correctly with dark theme and red accents
- ✅ Configured deployment settings for production (autoscale deployment)
- ✅ Server running successfully with bot initialized
- ✅ Chat functionality tested and working correctly

## Project Architecture

### Backend (FastAPI)
- **Main app**: `main.py` - FastAPI application
- **Bot logic**: `bot.py` - SportsBot class with Gemini AI
- **Context**: `context.txt` - Sports knowledge base
- **Configuration**: `.env` - Environment variables
- **Port**: 5000 (frontend and API on same port)

### Backend Endpoints
- `GET /` - Serves the frontend HTML
- `GET /health` - Health check endpoint
- `POST /chat` - Chat endpoint for user queries
- `POST /keep-alive` - Keep-alive endpoint for server monitoring

### Frontend 
- **File**: `static/index.html` - Single-page application
- **Theme**: Dark theme with red accents
- **Features**: Real-time chat, typing indicators, smooth animations
- **Integration**: Calls backend API on the same domain

### AI Integration
- **Platform**: Google Gemini AI (via google-genai SDK)
- **Model**: gemini-2.5-flash
- **Features**: 
  - Smart small talk detection
  - Context-aware responses from knowledge base
  - Profanity filtering
  - Committee comparison handling
  - Hinglish support

### Key Features
- **Small Talk**: Recognizes greetings and responds naturally
- **Context Matching**: Uses knowledge base for accurate answers
- **Fallback Responses**: Graceful handling when information unavailable
- **Response Validation**: Ensures appropriate and accurate responses

## Environment Variables
- `GEMINI_API_KEY` - Google Gemini API key
- `GEMINI_MODEL` - Model to use (default: gemini-2.5-flash)
- `API_TEMPERATURE` - AI temperature setting (default: 0.3)
- `API_MAX_TOKENS` - Max response tokens (default: 500)
- `HOST` - Server host (0.0.0.0)
- `PORT` - Server port (5000)
- `RELOAD` - Auto-reload on code changes (true for development)
- `ALLOWED_ORIGINS` - CORS allowed origins

## Dependencies
- fastapi==0.115.5 - Modern web framework
- uvicorn==0.32.0 - ASGI server
- pydantic==2.10.4 - Data validation
- google-genai - Google Gemini AI SDK
- python-dotenv==1.0.1 - Environment variable management
- requests==2.32.3 - HTTP library

## Workflow Configuration
- **Command**: `uvicorn main:app --host 0.0.0.0 --port 5000 --reload`
- **Port**: 5000
- **Output**: Webview (frontend)
- **Auto-reload**: Enabled for development

## Technical Notes
- FastAPI provides automatic API documentation at `/docs`
- Bot uses text fingerprinting for context matching
- Small talk detection uses regex patterns
- Frontend served with cache-busting headers
- CORS configured for multiple origins
- All responses validated before sending

## File Structure
```
├── main.py              # FastAPI application
├── bot.py               # SportsBot class
├── context.txt          # Knowledge base
├── .env                 # Environment variables (not committed to Git)
├── static/
│   └── index.html       # Frontend application
├── requirements.txt     # Python dependencies
├── vercel.json          # Vercel deployment config
└── replit.md            # This file
```

## Vercel Deployment

### Important: Environment Variables Required!
The chatbot **will not work** on Vercel without setting environment variables. If you're getting 500 errors or "Something went wrong!" messages, follow these steps:

### Deployment Steps:
1. Push your code to GitHub
2. Connect GitHub repo to Vercel
3. **CRITICAL**: In Vercel project settings → Environment Variables, add:
   - `GEMINI_API_KEY` - Your Google Gemini API key (REQUIRED)
   - `GEMINI_MODEL` - gemini-2.5-flash (optional, defaults to this)
   - `API_TEMPERATURE` - 0.3 (optional)
   - `API_MAX_TOKENS` - 500 (optional)
4. Redeploy the project after adding environment variables

### Troubleshooting Vercel Deployment:
- **Error: 500 status / "Something went wrong!"** 
  → GEMINI_API_KEY is not set in Vercel environment variables
  → Go to Project Settings → Environment Variables → Add GEMINI_API_KEY
  → Redeploy after adding the key
  
- **Error: "Missing key inputs argument"**
  → Same as above - add GEMINI_API_KEY to Vercel environment variables

- **Bot not responding**
  → Check Vercel function logs for detailed error messages
  → Verify API key is valid and has Gemini API access
