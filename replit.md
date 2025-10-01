# SPIT SportsCom Chatbot

## Project Overview
An AI-powered chatbot designed for SPIT SportsCom committee to help students with sports-related queries. The bot responds in Hinglish and provides information about:
- Agility Cup events and team formation
- Spoorthi sports fest details
- Committee selections and interviews
- Sports trials and venues
- General sports events and schedules

## Current Status
✅ **Successfully imported and running** - Ready for production deployment
- Python 3.11 environment with all dependencies installed
- Flask 2.3.3 backend running on port 5000 with 0.0.0.0 binding
- Dark theme frontend with red accents and chat functionality
- AI responses via Google Gemini with fallback system
- Deployment configuration set for autoscale with Gunicorn
- Workflow configured and running successfully

## Recent Changes (October 01, 2025)
- ✅ **Fresh GitHub import setup completed**
- ✅ Installed Python 3.11 and all dependencies
- ✅ Fixed requirements.txt duplicates and added Gunicorn
- ✅ Verified Flask application runs correctly on port 5000
- ✅ Tested frontend interface - working perfectly
- ✅ Configured production deployment with autoscale and Gunicorn
- ✅ **Project import complete and ready**

## Project Architecture

### Backend (Flask)
- **Main app**: `app.py` - Primary Flask application
- **API endpoint**: `/chat` - Handles user messages and AI responses
- **Health check**: `/health` - Application status endpoint
- **Static serving**: `/` - Serves the frontend interface
- **Port**: 5000 (frontend on 0.0.0.0)

### Frontend 
- **File**: `static/index.html` - Single-page application
- **Theme**: Dark theme with red accents
- **Features**: Typing indicators, smooth animations, real-time chat
- **Cache-busting**: Headers configured to prevent stale content

### AI Integration
- **Platform**: Google Gemini AI via python_gemini integration
- **Fallback**: Rule-based responses when API key unavailable
- **Context**: Uses processed sports committee chat history
- **Validation**: Response length limits and event isolation rules

### Data Files
- `system_prompt.txt` - AI system instructions
- `processed_chunks.txt` - Sports chat history for context
- `requirements.txt` - Python dependencies
- `vercel.json` - Legacy deployment configuration

## Deployment Settings
- **Target**: Autoscale (stateless web application)
- **Runtime**: Python 3.11 with Gunicorn WSGI server
- **Port**: 5000 (frontend only)
- **Workers**: 2 Gunicorn workers with port reuse
- **Command**: `gunicorn --bind=0.0.0.0:5000 --reuse-port --workers=2 app:app`

## Environment Variables
- `GEMINI_API_KEY` - Google Gemini API key (optional)
  - Can be set via Replit Secrets for AI responses
  - Graceful fallback to rule-based responses when unavailable
  - No hardcoded keys in codebase

## Dependencies
- Flask 2.3.3 - Web framework
- Flask-CORS 4.0.0 - CORS support
- google-generativeai 0.8.5 - Gemini AI SDK
- python-dotenv 1.0.1 - Environment variable management
- requests 2.32.5 - HTTP library
- gunicorn 21.2.0 - Production WSGI server

## Technical Notes
- Application includes text fingerprinting for context matching
- Response validation ensures proper event isolation
- Cache-busting headers prevent reload issues in Replit iframe
- All static files served with proper MIME types
- Development server runs with debug mode for easier testing
- Production deployment uses Gunicorn for better performance
