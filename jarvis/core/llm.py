import google.generativeai as genai
import os
import json
import time

class KeyManager:
    """Manages multiple API keys and their quota states."""
    def __init__(self, keys):
        self.keys = keys if isinstance(keys, list) else [keys]
        self.current_key_index = 0
        self.exhausted_keys = {} # key -> cleanup_timestamp
        self.cooldown_period = 3600 # 1 hour cool down for 429/404 errors
    
    def get_current_key(self):
        if not self.keys:
            return None
        now = time.time()
        # Cleanup expired entries
        self.exhausted_keys = {k: ts for k, ts in self.exhausted_keys.items() if now < ts}
        
        for i in range(len(self.keys)):
            idx = (self.current_key_index + i) % len(self.keys)
            key = self.keys[idx]
            if key not in self.exhausted_keys:
                self.current_key_index = idx
                return key
        return None

    def mark_exhausted(self, key):
        self.exhausted_keys[key] = time.time() + self.cooldown_period
        self.rotate()

    def rotate(self):
        if self.keys:
            self.current_key_index = (self.current_key_index + 1) % len(self.keys)

class LLM:
    def __init__(self):
        self.keys = self._load_api_keys()
        self.key_manager = KeyManager(self.keys)
        # Prioritize 2.5-flash as it's the newest confirmed model for new projects
        self.models_to_try = [
            'models/gemini-2.5-flash',
            'models/gemini-1.5-flash',
            'models/gemini-1.5-pro',
            'models/gemini-pro',
            'models/gemini-2.0-flash-exp'
        ]
        self.current_model_index = 0
        self.model = None
        self.chat = None
        self._initialize_llm()

    def _initialize_llm(self, rotate_key=False, try_next_model=False):
        """Initialize LLM with current or next key/model."""
        if rotate_key:
            current_key = self.key_manager.get_current_key()
            if current_key:
                self.key_manager.mark_exhausted(current_key)
            self.current_model_index = 0
        
        if try_next_model:
            self.current_model_index += 1
            if self.current_model_index >= len(self.models_to_try):
                return self._initialize_llm(rotate_key=True)

        key = self.key_manager.get_current_key()
        if not key:
            return False
        
        try:
            genai.configure(api_key=key, transport='rest')
            model_name = self.models_to_try[self.current_model_index]
            self.model = genai.GenerativeModel(model_name)
            self.chat = self.model.start_chat(history=[])
            return True
        except Exception:
            return self._initialize_llm(try_next_model=True)

    def _load_api_keys(self):
        try:
            secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'secrets.json')
            if os.path.exists(secrets_path):
                with open(secrets_path, 'r') as f:
                    secrets = json.load(f)
                    keys = secrets.get('GEMINI_API_KEYS') or secrets.get('GEMINI_API_KEY')
                    if isinstance(keys, str):
                        return [keys]
                    return keys or []
        except Exception:
            pass
        return []

    def chat_with_context(self, user_input, context, system_instruction=None, retry_count=0):
        if not self.model or not self.chat:
            if not self._initialize_llm():
                return "All AI quotas are full. Please add more API keys."

        full_prompt = (f"System: {system_instruction}\n" if system_instruction else "") + \
                      f"Context: {context}\nUser: {user_input}"

        try:
            response = self.chat.send_message(full_prompt)
            return response.text
        except Exception as e:
            err = str(e)
            if ("429" in err or "404" in err or "quota" in err.lower() or "limit" in err.lower()):
                if retry_count < len(self.keys) * len(self.models_to_try):
                    if self._initialize_llm(try_next_model=True):
                        return self.chat_with_context(user_input, context, system_instruction, retry_count + 1)
            return f"Thinking error: {e}"

    def analyze_image(self, image_path, prompt, retry_count=0):
        if not self.model:
            if not self._initialize_llm():
                return "AI unavailable."
        try:
            from PIL import Image
            img = Image.open(image_path)
            response = self.model.generate_content([prompt, img])
            return response.text
        except Exception as e:
            err = str(e)
            if ("429" in err or "404" in err or "quota" in err.lower()) and retry_count < 10:
                if self._initialize_llm(try_next_model=True):
                    return self.analyze_image(image_path, prompt, retry_count + 1)
            return f"Vision error: {e}"
