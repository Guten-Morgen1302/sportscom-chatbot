from pathlib import Path
import os

from dotenv import load_dotenv
load_dotenv()
from google import genai
from google.genai.types import GenerateContentConfig

import re, random


class SportsBot:
    def __init__(self, context_file="context.txt"):
        # Load the whole context from file
        path = Path(context_file)
        if not path.exists():
            raise FileNotFoundError(f"Context file not found: {context_file}")
        self.context = path.read_text(encoding="utf-8")
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.temperature=float(os.getenv("API_TEMPERATURE", "0.3"))
        self.max_tokens=int(os.getenv("API_MAX_TOKENS", "500"))
        self.referer=os.getenv("HTTP_REFERER", "https://sports-committee-bot.com")
        self.system_rules = (
            "You are a knowledgeable sports assistant. Use the knowledge below to answer.\n"
            "Be clear and concise; think like a senior student member of the sports committee.\n"
            "If the user message contains any sort of profanity or abusive or improper language, reply exactly:\n"
            "\"Please use proper language.\"\n"
            "If user message is a greeting/pleasantry/small-talk (e.g. 'hi', 'hello', 'how are you', 'thanks', 'bye'), "
            "reply naturally in 1 short line and DO NOT use any knowledge provided.\n"
            "If any other committee is mentioned, like Finance and Economics Club(FEC), Entrepreneurship Cell(E-Cell), Computer Society of India(CSI), Rotaract Club(RC), Drone Research Club(DRC), IETE, IEEE, ASCES, FACE, FETS, Speaker's club or SPCG, "
            "redirect the conversation to Sports committee.\n"
            "If the user compares Sports committee with other committees, emphasize why Sports committee is the best.\n"
            "Make some witty, non-offensive, humorous remarks about the other committees Make sure it is NOT offensive or rude.\n"
            "When responding to such messages, do NOT mention their names, just refer to them as 'other committees' or 'they' or 'them'.\n"
            "Do not tolerate any negative comments about Sports committee or any other committee. If someone badmouths any committee, explain how every committee is different, but no committee is bad.\n"
            "Solve doubts of new students. Keep output simple text.\n"
            "For actual questions: Do not add info beyond the knowledge provided.\n"
            "If you don't know the answer, reply exactly: \"Ask this on sports update group\".\n"
            "If the question involves dates and dates aren't in the knowledge, reply exactly:\n"
            "\"Seniors will post the final dates on official class groups.\"\n"
            "STRICTLY DO NOT mention any knowledge base or context."
            "# ACCEPT ANSWERS IN HINGLISH IF THE QUESTION IS IN HINGLISH.\n"
            "IF THE QUESTION IS IN HINGLISH, ANSWER IN HINGLISH."
            
        )
        
        self._small_talk_regexes = [
            re.compile(r"^\s*(hi|hello|hey|yo|hola|namaste)\s*[!.]*$", re.I),
            re.compile(r"^\s*(good\s*(morning|afternoon|evening|night))\s*[!.]*$", re.I),
            re.compile(r"^\s*(how\s*are\s*you|hru|how'?s\s*it\s*going)\s*\??\s*$", re.I),
            re.compile(r"^\s*(thanks|thank\s*you|ty|thx)\s*[!.]*$", re.I),
            re.compile(r"^\s*(ok|okay|cool|nice)\s*[!.]*$", re.I),
            re.compile(r"^\s*(bye|goodbye|see\s*ya|see\s*you)\s*[!.]*$", re.I),
        ]
        
    def _is_small_talk(self, message: str) -> bool:
        return any(rx.match(message) for rx in self._small_talk_regexes)
    
    def _small_talk_reply(self, msg: str) -> str:
        m = msg.lower().strip()
        if any(w in m for w in ["hi", "hello", "hey", "yo", "hola", "namaste", "good morning", "good afternoon", "good evening"]):
            return random.choice(["Hey! 👋", "Hello! 👋", "Hi! 👋"])
        if "how are you" in m or "hru" in m or "how's it going" in m:
            return random.choice(["All good! How can I help with sports info?", "Doing great!! What do you need help with?"])
        if "thanks" in m or "thank you" in m or "ty" in m or "thx" in m:
            return random.choice(["Anytime!", "You're welcome!", "Glad to help!"])
        if any(w in m for w in ["ok", "okay", "cool", "nice"]):
            return random.choice(["👍", "Got it!", "Cool."])
        if any(w in m for w in ["bye", "goodbye", "see ya", "see you"]):
            return random.choice(["Bye! 👋", "See you around!", "Take care!"])
        return "Hey! How can I help with sports info?"

    def query_gemini(self, user_message: str) -> str:
        # Use provided config or defaults from environment

        # headers = {
        #     "Authorization": f"Bearer {api_key}",
        #     "HTTP-Referer": referer,
        #     "Content-Type": "application/json"
        # }
        
        prompt = f"""{self.system_rules}
        Knowledge: {self.context}
        
        Question: {user_message}
        
        Please provide a clear, concise answer citing the specific document source when possible."""

        # data = {
        #     "model": model,  
        #     "temperature": temperature,        # controls creativity (0 = strict, 1 = creative)
        #     "max_tokens": max_tokens,         # controls max length of response
        #     "messages": [
        #         {"role": "user", "content": prompt}
        #     ]
        # }

        response = self.client.models.generate_content(
            model=self.model, 
            contents=prompt, 
            config=GenerateContentConfig(
                temperature=self.temperature, 
                max_output_tokens=self.max_tokens)
            )
        return (response.text or "").strip()

    def get_response(self, user_input: str) -> str:
        if self._is_small_talk(user_input):
            return self._small_talk_reply(user_input)
        return self.query_gemini(user_input)


def main():
    print("Initializing Sports Event Assistant Bot...")
    bot = SportsBot("context.txt")

    # Replace with your Gemini API key
    # API_KEY = "AIzaSyDXHa5g3QLhOMUZeioa_y2L4giVlyYDOBg"
    
    print("\nSports Event Assistant Bot Ready! (type 'quit' to exit)")
    print("-" * 50)
    
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() == 'quit':
            break
            
        try:
            response = bot.get_response(user_input)
            print(f"\nQuestion: {user_input}")   # 👈 Show input first
            print(f"Answer: {response}")        # 👈 Then show output
        except Exception as e:
            print(f"\nError: {str(e)}")


if __name__ == "__main__":
    main()