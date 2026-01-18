import google.generativeai as genai
import os
import json
import time
from datetime import datetime, timedelta

class LLM:
    """Lean Gemini client with a hard Circuit Breaker."""
    
    def __init__(self):
        self.keys = self._load_api_keys()
        self.primary_key = self.keys[0] if self.keys else None
        self.model_name = 'models/gemini-2.0-flash-exp' # Updated to available model
        
        # Circuit Breaker state
        self.is_disabled = False
        self.disabled_until = None
        
        self.model = None
        self.chat = None
        self._initialize_llm()

    def _initialize_llm(self):
        """Initialize LLM once. No rotation."""
        if not self.primary_key:
            print("ALERT: No Gemini API key found.")
            return False
            
        try:
            genai.configure(api_key=self.primary_key, transport='rest')
            self.model = genai.GenerativeModel(self.model_name)
            self.chat = self.model.start_chat(history=[])
            return True
        except Exception as e:
            print(f"FAILED to initialize Gemini: {e}")
            return False

    def _load_api_keys(self):
        try:
            secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'secrets.json')
            if os.path.exists(secrets_path):
                with open(secrets_path, 'r') as f:
                    secrets = json.load(f)
                    keys = secrets.get('GEMINI_API_KEYS') or secrets.get('GEMINI_API_KEY')
                    if isinstance(keys, str): return [keys]
                    return keys or []
        except: pass
        return []

    def check_circuit_breaker(self):
        """Check if Gemini is currently locked out."""
        if self.is_disabled:
            if datetime.now() < self.disabled_until:
                return True
            else:
                self.is_disabled = False
                print("DEBUG: Gemini Circuit Breaker reset. Retrying web access.")
        return False

    def trigger_circuit_breaker(self, duration_mins=15):
        """Disable Gemini for a duration."""
        self.is_disabled = True
        self.disabled_until = datetime.now() + timedelta(minutes=duration_mins)
        print(f"CRITICAL: Gemini disabled due to quota for {duration_mins} minutes.")

    def chat_with_context(self, user_input, context, system_instruction=None):
        if self.check_circuit_breaker():
            return "CIRCUIT_BREAKER_ACTIVE"

        if not self.model: 
            return "GEMINI_NOT_INITIALIZED"

        full_prompt = (f"System: {system_instruction}\n" if system_instruction else "") + \
                      f"Context: {context}\nUser: {user_input}"

        try:
            response = self.chat.send_message(full_prompt)
            return response.text
        except Exception as e:
            err = str(e).lower()
            if any(x in err for x in ["429", "quota", "limit", "exhausted"]):
                self.trigger_circuit_breaker()
                return "QUOTA_EXCEEDED"
            return f"Thinking error: {e}"

    def analyze_image(self, image_path, prompt):
        if self.check_circuit_breaker():
            return "CIRCUIT_BREAKER_ACTIVE"
        try:
            from PIL import Image
            img = Image.open(image_path)
            response = self.model.generate_content([prompt, img])
            return response.text
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                self.trigger_circuit_breaker()
                return "QUOTA_EXCEEDED"
            return f"Vision error: {e}"
