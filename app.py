from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
CORS(app)

# Load system prompt
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# Load chat data
with open("processed_chunks.txt", "r", encoding="utf-8") as f:
    chat_data = f.read()

# Split into chunks for easier searching
chunks = [chunk.strip() for chunk in chat_data.split('\n\n') if chunk.strip()]

def find_relevant_context(user_message):
    """
    Find relevant context using basic text matching
    """
    user_message_lower = user_message.lower()
    relevant_chunks = []
    
    # Keywords to look for based on common queries
    keywords = {
        'agility': ['agility', 'cup'],
        'spoorthi': ['spoorthi', 'inter-college'],
        'committee': ['committee', 'subcom', 'selection'],
        'trials': ['trial', 'selection', 'captain'],
        'basketball': ['basketball', 'wadia'],
        'cricket': ['cricket', 'bhavan'],
        'football': ['football', 'bhavan'],
        'badminton': ['badminton', 'asc'],
        'chess': ['chess', 'fide'],
        'table tennis': ['tt', 'table tennis', 'gymkhana'],
        'volleyball': ['volleyball'],
        'dates': ['date', 'when', 'schedule'],
        'participation': ['participate', 'join', 'take part'],
        'venues': ['venue', 'court', 'ground', 'where']
    }
    
    # Find matching chunks
    for chunk in chunks:
        chunk_lower = chunk.lower()
        
        # Direct keyword matching
        for category, words in keywords.items():
            if any(word in user_message_lower for word in words):
                if any(word in chunk_lower for word in words):
                    relevant_chunks.append(chunk)
                    break
    
    # If no specific matches, look for general context
    if not relevant_chunks:
        # Look for chunks that contain similar words
        words_in_query = set(re.findall(r'\b\w+\b', user_message_lower))
        for chunk in chunks[:10]:  # Just check first 10 chunks as fallback
            chunk_words = set(re.findall(r'\b\w+\b', chunk.lower()))
            if len(words_in_query.intersection(chunk_words)) >= 2:
                relevant_chunks.append(chunk)
    
    return relevant_chunks[:3]  # Return top 3 matches

def query_gemini_model(user_message, context=None):
    """
    Query Gemini model with context
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return generate_fallback_response(user_message, context)
    
    try:
        # Construct prompt with system instructions and context
        if context:
            context_text = "\n".join(context)
            prompt = f"""
{SYSTEM_PROMPT}

Context from SportsCom chat history:
{context_text}

User: {user_message}

Respond as a SPIT SportsCom senior student in Hinglish, following the rules strictly. Keep it under 800 characters unless user says "detail".
"""
        else:
            prompt = f"""
{SYSTEM_PROMPT}

User: {user_message}

Respond as a SPIT SportsCom senior student in Hinglish. If you don't know, say "Ask this on sports update group".
"""

        # Make API call to Gemini
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        headers = {
            'Content-Type': 'application/json',
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        response = requests.post(f"{url}?key={api_key}", headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text']
        
        return generate_fallback_response(user_message, context)
        
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return generate_fallback_response(user_message, context)

def generate_fallback_response(user_message, context):
    """
    Generate fallback response when Gemini is not available
    """
    user_message_lower = user_message.lower()
    
    # Basic rule-based responses based on system prompt
    if any(word in user_message_lower for word in ['agility', 'cup']):
        return "Agility Cup open hai bro—apni team banao, mix branches/years chalega. November first week tentative hai. Final dates class groups pe aayenge."
    
    elif any(word in user_message_lower for word in ['spoorthi']):
        return "Spoorthi Feb-Mar mein hai. Team sports ke liye college team selection chahiye, chess/TT jaise solos jab announce honge tab."
    
    elif any(word in user_message_lower for word in ['committee', 'join', 'selection']):
        return "Committee selections after 10th October. Forms kal se float ho jayenge. Interview hogi but bakchodiyan bhi hongi, dw."
    
    elif any(word in user_message_lower for word in ['date', 'when', 'schedule']):
        return "Seniors will post the final dates on official class groups."
    
    elif any(word in user_message_lower for word in ['basketball']):
        return "Basketball trials early Oct. Venue: Wadia court."
    
    elif any(word in user_message_lower for word in ['cricket', 'football']):
        return "Cricket/Football trials tentatively 1st week Nov. Venue: Bhavan's ground (post-rains maintenance dependent)."
    
    elif any(word in user_message_lower for word in ['badminton']):
        return "Badminton venue: ASC courts (online booking available)."
    
    elif any(word in user_message_lower for word in ['chess']):
        return "FIDE Chess tournament bhi hai. Chess teams technical hai, practice groups banenge."
    
    elif any(word in user_message_lower for word in ['venue', 'where', 'court']):
        return "Basketball: Wadia court, Cricket/Football: Bhavan's ground, Badminton: ASC courts, TT/Carrom: Gymkhana."
    
    else:
        return "Ask this on sports update group."

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json.get("message", "").strip()
        
        if not user_input:
            return jsonify({"response": "Kuch toh bolo yaar!"})
        
        # Find relevant context
        context = find_relevant_context(user_input)
        
        # Generate response
        ai_response = query_gemini_model(user_input, context)
        
        return jsonify({"response": ai_response})
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({"response": "Something went wrong. Ask this on sports update group."})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "SPIT SportsCom Bot is running!"})

if __name__ == '__main__':
    print("Starting SPIT SportsCom Bot...")
    app.run(debug=True, host='0.0.0.0', port=5000)