# SPIT SportsCom Chatbot

## Overview

A Flask-based chatbot application designed for SPIT (Sardar Patel Institute of Technology) Sports Committee. The bot provides information about sports events, committee participation, and answers student queries using Google's Gemini AI. It processes pre-loaded chat data to provide contextually relevant responses about sports committee activities, events like Agility Cup, Spoorthi, Half-Marathon, FIDE Chess, and GC Sports.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework with CORS enabled for cross-origin requests
- **AI Integration**: Google Gemini 2.5-flash model for natural language processing and response generation
- **Text Processing**: Custom text fingerprinting system using TF-IDF-like approach for similarity matching
- **Data Storage**: File-based storage system using plain text files for chat data and system prompts

### Response Generation System
- **Prompt Engineering**: Structured system prompt defining bot persona as senior SPIT student volunteer
- **Context Retrieval**: Similarity-based chunk retrieval from processed chat conversations
- **Response Constraints**: Character limits (800-1200) optimized for Vercel hosting with stateless operation

### Text Similarity Engine
- **Fingerprinting**: Word frequency-based fingerprinting using Counter collections
- **Matching Algorithm**: Intersection-based similarity scoring for relevant context retrieval
- **Chunk Processing**: Pre-computed fingerprints for efficient real-time matching

### Frontend Architecture
- **Interface**: Simple HTML/CSS chat interface with gradient styling
- **Design**: Responsive design with mobile-first approach
- **User Experience**: Clean chat container with header and message display area

### Data Processing
- **Chat Data**: Preprocessed conversation chunks from sports committee discussions
- **System Prompts**: Structured instruction sets for bot behavior and response formatting
- **Language Support**: Hinglish (Hindi-English mix) communication style

## External Dependencies

### AI Services
- **Google Generative AI**: Gemini 2.5-flash model for natural language understanding and generation with safety settings
- **API Authentication**: Environment-based API key management via Replit Secrets

### Python Libraries
- **Flask**: Web framework for API endpoints and request handling
- **Flask-CORS**: Cross-origin resource sharing support
- **python-dotenv**: Environment variable management for secure configuration
- **google-generativeai**: Official Google AI client library with safety controls
- **Collections**: Built-in Counter class for text fingerprinting and similarity computation
- **Regex**: Text processing and pattern matching for contextual search

### Development Tools
- **Environment Variables**: Secure API key storage using .env files
- **Text Encoding**: UTF-8 encoding for multilingual content support

### Hosting Considerations
- **Vercel Optimization**: Stateless design with response size constraints
- **Resource Management**: Efficient memory usage with pre-computed embeddings
- **Performance**: Fast response times through cached text fingerprints