from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import re
import os
from dotenv import load_dotenv
import google.generativeai as genai
import hashlib
from collections import Counter

load_dotenv()

app = Flask(__name__)
CORS(app)

# Load system prompt
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# Load chat data
with open("processed_chunks.txt", "r", encoding="utf-8") as f:
    chat_data = f.read()

# Initialize Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

# Split into chunks for easier searching
chunks = [chunk.strip() for chunk in chat_data.split('\n\n') if chunk.strip()]

# Create simple embeddings using TF-IDF like approach
def create_text_fingerprint(text):
    """Create a simple text fingerprint using word frequency and patterns"""
    words = re.findall(r'\b\w+\b', text.lower())
    word_counts = Counter(words)
    # Create a hash-based fingerprint
    fingerprint = {}
    for word, count in word_counts.most_common(50):  # Top 50 words
        fingerprint[word] = count
    return fingerprint

# Pre-compute fingerprints for all chunks
chunk_fingerprints = [create_text_fingerprint(chunk) for chunk in chunks]

def compute_similarity_score(fingerprint1, fingerprint2):
    """Compute similarity between two text fingerprints"""
    common_words = set(fingerprint1.keys()).intersection(set(fingerprint2.keys()))
    if not common_words:
        return 0.0
    
    score = 0.0
    total_weight = 0.0
    
    for word in common_words:
        # Weight by frequency in both texts
        weight = min(fingerprint1[word], fingerprint2[word])
        score += weight
        total_weight += weight
    
    # Normalize by total words in query
    query_total = sum(fingerprint1.values())
    return score / max(query_total, 1) if query_total > 0 else 0.0

def find_relevant_context(user_message):
    """
    Find relevant context using improved semantic similarity
    """
    user_fingerprint = create_text_fingerprint(user_message)
    chunk_scores = []
    
    # Compute similarity scores for all chunks
    for i, chunk_fingerprint in enumerate(chunk_fingerprints):
        similarity = compute_similarity_score(user_fingerprint, chunk_fingerprint)
        if similarity > 0.1:  # Minimum similarity threshold
            chunk_scores.append((similarity, i, chunks[i]))
    
    # Sort by similarity score and return top matches
    chunk_scores.sort(reverse=True, key=lambda x: x[0])
    return [chunk for _, _, chunk in chunk_scores[:3]]

def validate_response_rules(response, user_message):
    """Validate response follows system prompt rules"""
    user_lower = user_message.lower()
    response_lower = response.lower()
    
    # Check event isolation rules
    events = {'agility', 'spoorthi', 'marathon'}
    user_event = None
    for event in events:
        if event in user_lower:
            user_event = event
            break
    
    if user_event:
        other_events = events - {user_event}
        for other_event in other_events:
            if other_event in response_lower:
                return False, f"Response mentions {other_event} when user asked about {user_event}"
    
    # Check length limit (800 chars unless "detail" requested, then 1200 chars max)
    if "detail" in user_lower:
        if len(response) > 1200:
            return False, "Response exceeds 1200 character limit for detailed responses"
    else:
        if len(response) > 800:
            return False, "Response exceeds 800 character limit"
    
    return True, "Valid"

def query_gemini_model(user_message, context=None):
    """
    Query Gemini model with proper safety checks
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

        # Configure safety settings
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
        
        # Generate response
        response = model.generate_content(
            prompt,
            safety_settings=safety_settings,
            generation_config=genai.GenerationConfig(
                max_output_tokens=1000,
                temperature=0.7,
                top_k=40,
                top_p=0.8,
            )
        )
        
        if response.text:
            # Validate response follows rules
            is_valid, validation_msg = validate_response_rules(response.text, user_message)
            if is_valid:
                return response.text
            else:
                print(f"Response validation failed: {validation_msg}")
                return generate_fallback_response(user_message, context)
        
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

@app.route('/')
def index():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return html_content
    except FileNotFoundError:
        return jsonify({"error": "Frontend not found"}), 404

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "SPIT SportsCom Bot is running!"})

if __name__ == '__main__':
    print("Starting SPIT SportsCom Bot...")
    app.run(debug=True, host='0.0.0.0', port=5000)