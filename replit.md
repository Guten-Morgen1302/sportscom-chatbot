# SPIT SportsCom Elite Chatbot

## Project Overview
A sophisticated AI-powered chatbot designed for SPIT SportsCom committee to help students with sports-related queries. The bot responds in Hinglish and provides information about:
- Agility Cup events and team formation
- Spoorthi sports fest details
- Committee selections and interviews
- Sports trials and venues
- General sports events and schedules

## Current Status
✅ **Fully functional** - Ready for production deployment
- Flask backend running on port 5000
- Beautiful Elite-themed frontend with dark mode
- Chat functionality working with fallback responses
- Deployment configuration set for autoscale

## Recent Changes (September 29, 2025)
- ✅ Installed Python 3.11 and all dependencies
- ✅ Fixed loading screen animation issue
- ✅ Added cache-busting headers for Replit environment
- ✅ Configured Flask app for 0.0.0.0:5000 binding
- ✅ Set up deployment configuration for production
- ✅ Verified chat API functionality

## Project Architecture

### Backend (Flask)
- **Main app**: `app.py` - Primary Flask application
- **API endpoint**: `/chat` - Handles user messages and AI responses
- **Health check**: `/health` - Application status endpoint
- **Static serving**: `/` - Serves the frontend interface

### Frontend 
- **File**: `static/index.html` - Single-page application
- **Theme**: Elite dark theme with animations
- **Features**: Loading screen, typing indicators, smooth animations
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
- `vercel.json` - Deployment configuration (legacy)

## User Preferences
- Hinglish communication style preferred
- Sports-focused responses with college context
- Fallback to "Ask this on sports update group" for unknown queries

## Deployment Settings
- **Target**: Autoscale (stateless web application)
- **Runtime**: Python 3.11
- **Port**: 5000 (frontend only)
- **Command**: `python app.py`

## Environment Variables
- `GEMINI_API_KEY` - Google Gemini API key (optional - has fallbacks)

## Known Issues
- LSP diagnostics show import errors (cosmetic only - app runs fine)
- Loading screen animation required JavaScript fix for proper removal

## Technical Notes
- Application includes sophisticated text fingerprinting for context matching
- Response validation ensures proper event isolation
- Cache-busting headers prevent reload issues in Replit iframe environment
- Beautiful particle system and gradient animations for premium feel