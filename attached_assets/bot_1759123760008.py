from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os

from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes and origins

# Load your chat file and split into chunks
with open("processed_chunks.txt", "r", encoding="utf-8") as f:
    chat_text = f.read()

# Split chat text into chunks (approx 500 chars each)
chunks = [chat_text[i:i+500] for i in range(0, len(chat_text), 500)]

# Load Sentence transformer model (free and open-source)
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Generate embeddings for each chunk
chunk_embeddings = embedder.encode(chunks, convert_to_numpy=True)

# Normalize embeddings for cosine similarity
chunk_embeddings = chunk_embeddings / np.linalg.norm(chunk_embeddings, axis=1, keepdims=True)

# Build FAISS index for efficient similarity search
dimension = chunk_embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)  # Inner Product = cosine similarity because vectors are normalized
index.add(chunk_embeddings)

def query_gemini_model(user_message, context=None):
    # Dummy implementation - replace with your Gemini 2.5 Flash API call
    # Combine context and user message for prompt construction
    if context:
        prompt = f"Context: {context}\nUser: {user_message}\nChatbot:"
    else:
        prompt = user_message
    # Simulate AI response
    return f"[Simulated Gemini Response Based on Context: {context[:100]}...]"

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message", "")

    # Get user input embedding and normalize
    query_embedding = embedder.encode([user_input], convert_to_numpy=True)
    query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)

    # Search top 3 relevant chunks from chat content
    D, I = index.search(query_embedding, k=3)  # I contains indices of top chunks

    # Combine top chunks as context
    context = " ".join([chunks[i] for i in I[0]])

    # Query Gemini model with context
    ai_response = query_gemini_model(user_input, context)

    return jsonify({"response": ai_response})

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True)
