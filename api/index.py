from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os
from dotenv import load_dotenv
import google.generativeai as genai
import hashlib
from collections import Counter

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Load system prompt from root directory
try:
    with open("../system_prompt.txt", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    with open("system_prompt.txt", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()

# Load chat data from root directory  
try:
    with open("../processed_chunks.txt", "r", encoding="utf-8") as f:
        chat_data = f.read()
except FileNotFoundError:
    with open("processed_chunks.txt", "r", encoding="utf-8") as f:
        chat_data = f.read()

# Initialize Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
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
    """Find relevant context using improved semantic similarity"""
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
    """Query Gemini model with proper safety checks"""
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
    """Generate fallback response when Gemini is not available"""
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

# Serve the frontend
@app.route('/')
def index():
    """Serve the chat interface"""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SPIT SportsCom Bot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .chat-container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 90%;
            max-width: 600px;
            height: 80vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #ff6b6b, #ee5a24);
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .chat-header h1 {
            font-size: 24px;
            margin-bottom: 5px;
        }
        
        .chat-header p {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background-color: #f8f9fa;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 12px 16px;
            border-radius: 20px;
            max-width: 80%;
            word-wrap: break-word;
            animation: fadeIn 0.3s ease-in;
        }
        
        .user-message {
            background: #007bff;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        
        .bot-message {
            background: white;
            color: #333;
            border: 2px solid #e9ecef;
            margin-right: auto;
        }
        
        .chat-input {
            padding: 20px;
            background: white;
            border-top: 1px solid #e9ecef;
            display: flex;
            gap: 10px;
        }
        
        .chat-input input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e9ecef;
            border-radius: 25px;
            outline: none;
            font-size: 16px;
        }
        
        .chat-input input:focus {
            border-color: #007bff;
        }
        
        .chat-input button {
            background: #007bff;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }
        
        .chat-input button:hover {
            background: #0056b3;
        }
        
        .chat-input button:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .typing-indicator {
            display: none;
            padding: 12px 16px;
            border-radius: 20px;
            background: white;
            border: 2px solid #e9ecef;
            margin-right: auto;
            max-width: 80%;
            margin-bottom: 15px;
        }
        
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        
        .typing-dots span {
            width: 8px;
            height: 8px;
            background: #999;
            border-radius: 50%;
            animation: typing 1.4s infinite ease-in-out;
        }
        
        .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
        .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes typing {
            0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🏏 SPIT SportsCom Bot</h1>
            <p>Tumhara senior sports committee member - Ask anything about SPIT sports!</p>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message bot-message">
                Hey! Main tumhara SportsCom senior hun. Kuch bhi poocho sports events, committees, trials ke baare mein. Agility Cup, Spoorthi, trials - sab kuch jaanta hun! 🔥
            </div>
        </div>
        
        <div class="typing-indicator" id="typingIndicator">
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
        
        <div class="chat-input">
            <input type="text" id="messageInput" placeholder="Type your message here... (in Hinglish!)" />
            <button onclick="sendMessage()" id="sendButton">Send</button>
        </div>
    </div>

    <script>
        const chatMessages = document.getElementById('chatMessages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const typingIndicator = document.getElementById('typingIndicator');

        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        function addMessage(message, isUser) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            messageDiv.textContent = message;
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function showTyping() {
            typingIndicator.style.display = 'block';
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function hideTyping() {
            typingIndicator.style.display = 'none';
        }

        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            // Disable input while processing
            messageInput.disabled = true;
            sendButton.disabled = true;

            // Add user message
            addMessage(message, true);
            messageInput.value = '';

            // Show typing indicator
            showTyping();

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message }),
                });

                const data = await response.json();
                
                // Hide typing indicator
                hideTyping();
                
                // Add bot response
                addMessage(data.response || 'Something went wrong!', false);

            } catch (error) {
                hideTyping();
                addMessage('Sorry, something went wrong! Ask this on sports update group.', false);
                console.error('Error:', error);
            }

            // Re-enable input
            messageInput.disabled = false;
            sendButton.disabled = false;
            messageInput.focus();
        }

        // Focus on input when page loads
        messageInput.focus();
    </script>
</body>
</html>"""
    return html_content

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

# For local development
if __name__ == '__main__':
    print("Starting SPIT SportsCom Bot...")
    app.run(debug=True, host='0.0.0.0', port=5000)