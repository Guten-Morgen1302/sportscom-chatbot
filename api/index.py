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

# Load system prompt and chat data
import os

# Get current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Load system prompt 
try:
    with open(os.path.join(current_dir, "system_prompt.txt"), "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    SYSTEM_PROMPT = """You are a helpful SportsCom senior at SPIT college. Respond in Hinglish style and help students with sports queries."""

# Load chat data
try:
    with open(os.path.join(current_dir, "processed_chunks.txt"), "r", encoding="utf-8") as f:
        chat_data = f.read()
except FileNotFoundError:
    chat_data = "No context data available"

# Initialize Gemini with safe fallback
api_key = os.environ.get("GEMINI_API_KEY")
model = None
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Gemini API initialized successfully")
    except Exception as e:
        print(f"⚠️ Gemini initialization failed: {e}")
else:
    print("ℹ️ No Gemini API key - using fallback responses")

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
    if not api_key or not model:
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

        # Generate response with safe configuration
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=800,
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
    """Serve the chat interface with updated design"""
    try:
        # Try to read the updated frontend from the parent directory
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        html_path = os.path.join(parent_dir, "static", "index.html")
        
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
                # Add cache-busting headers for deployment
                from flask import Response
                response = Response(html_content, mimetype='text/html')
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
                return response
    except Exception as e:
        print(f"Could not load static/index.html: {e}")
    
    # Fallback with updated UI
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SPIT SportsCom | Sports Assistant</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            /* Simple Red & Black Theme */
            --bg-primary: #000000;
            --bg-secondary: #111111;
            --bg-card: #1a1a1a;
            
            /* Text Colors */
            --text-primary: #ffffff;
            --text-secondary: #cccccc;
            --text-muted: #888888;
            
            /* Red Accent */
            --accent-primary: #dc2626;
            --accent-hover: #ef4444;
            
            /* Borders */
            --border-primary: #333333;
            --border-accent: #dc2626;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
        }

        .app-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }

        .chat-container {
            background: var(--bg-card);
            border: 1px solid var(--border-primary);
            border-radius: 12px;
            width: 100%;
            max-width: 800px;
            height: 90vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .chat-header {
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-primary);
            padding: 20px 24px;
        }

        .header-content {
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        }

        .header-logo {
            width: 40px;
            height: 40px;
            background: var(--accent-primary);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            color: white;
            font-weight: 600;
            margin-right: 12px;
        }

        .header-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--text-primary);
        }

        .header-subtitle {
            font-size: 0.9rem;
            color: var(--text-secondary);
            font-weight: 400;
            margin-top: 4px;
        }

        .chat-messages {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            background: var(--bg-primary);
        }

        .message {
            margin-bottom: 16px;
            padding: 12px 16px;
            border-radius: 8px;
            max-width: 80%;
            word-wrap: break-word;
        }

        .user-message {
            background: var(--accent-primary);
            color: white;
            margin-left: auto;
        }

        .bot-message {
            background: var(--bg-card);
            border: 1px solid var(--border-primary);
            color: var(--text-primary);
            margin-right: auto;
        }

        .chat-input {
            padding: 20px;
            background: var(--bg-secondary);
            border-top: 1px solid var(--border-primary);
        }

        .input-wrapper {
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }

        .input-container {
            flex: 1;
        }

        .input-field {
            width: 100%;
            background: var(--bg-card);
            border: 1px solid var(--border-primary);
            border-radius: 8px;
            padding: 12px 16px;
            color: var(--text-primary);
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s ease;
            resize: none;
            min-height: 44px;
            max-height: 120px;
        }

        .input-field:focus {
            border-color: var(--accent-primary);
        }

        .input-field::placeholder {
            color: var(--text-muted);
        }

        .send-button {
            background: var(--accent-primary);
            border: none;
            border-radius: 8px;
            padding: 12px 20px;
            color: white;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: background-color 0.2s ease;
            min-width: 100px;
            justify-content: center;
        }

        .send-button:hover {
            background: var(--accent-hover);
        }

        .welcome-message {
            text-align: center;
            padding: 32px;
            background: var(--bg-card);
            border: 1px solid var(--border-primary);
            border-radius: 8px;
            margin-bottom: 24px;
        }

        .welcome-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 12px;
        }

        .welcome-text {
            color: var(--text-secondary);
            line-height: 1.5;
            font-size: 0.95rem;
        }
    </style>
</head>
<body>
    <div class="app-container">
        <div class="chat-container">
            <div class="chat-header">
                <div class="header-content">
                    <div class="header-logo">
                        <i class="fas fa-trophy"></i>
                    </div>
                    <div>
                        <h1 class="header-title">SPIT SportsCom</h1>
                        <p class="header-subtitle">Your Sports Committee Assistant</p>
                    </div>
                </div>
            </div>

            <div class="chat-messages" id="chatMessages">
                <div class="welcome-message">
                    <h2 class="welcome-title">Welcome to SPIT SportsCom</h2>
                    <p class="welcome-text">Your sports committee assistant is ready! Ask about events, trials, committee selections, and venues.</p>
                </div>
                
                <div class="message bot-message">
                    <strong>🏆 SportsCom Bot</strong><br><br>
                    Hey! Main tumhara senior SportsCom member hun. Ask anything about sports events, trials, committee selections - sab kuch!<br><br>
                    Just type in Hinglish! 🚀
                </div>
            </div>

            <div class="chat-input">
                <div class="input-wrapper">
                    <div class="input-container">
                        <textarea 
                            id="messageInput" 
                            class="input-field" 
                            placeholder="Ask about sports events, trials, committees... Type in Hinglish!"
                            rows="1"
                        ></textarea>
                    </div>
                    <button onclick="sendMessage()" id="sendButton" class="send-button">
                        <i class="fas fa-paper-plane"></i>
                        <span>Send</span>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        const chatMessages = document.getElementById('chatMessages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');

        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        function addMessage(content, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            
            if (isUser) {
                const strongEl = document.createElement('strong');
                strongEl.textContent = 'You:';
                const contentEl = document.createElement('div');
                contentEl.textContent = content;
                
                messageDiv.appendChild(strongEl);
                messageDiv.appendChild(document.createElement('br'));
                messageDiv.appendChild(contentEl);
            } else {
                const contentEl = document.createElement('div');
                contentEl.textContent = content;
                messageDiv.appendChild(contentEl);
            }
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            messageInput.disabled = true;
            sendButton.disabled = true;
            sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Processing...</span>';

            addMessage(message, true);
            messageInput.value = '';

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message }),
                });

                const data = await response.json();
                const botResponse = data.response || 'Something went wrong! Ask this on sports update group.';
                addMessage('🏆 SportsCom Bot: ' + botResponse);

            } catch (error) {
                addMessage('❌ Connection failed! Please try again or ask on sports update group.');
                console.error('Error:', error);
            }

            sendButton.innerHTML = '<i class="fas fa-paper-plane"></i><span>Send</span>';
            messageInput.disabled = false;
            sendButton.disabled = false;
            messageInput.focus();
        }

        messageInput.focus();
    </script>
</body>
</html>"""
    
    from flask import Response
    response = Response(html_content, mimetype='text/html')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

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

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# For local development only - removed for Vercel deployment
# if __name__ == '__main__':
#     print("Starting SPIT SportsCom Bot...")
#     app.run(debug=True, host='0.0.0.0', port=5000)