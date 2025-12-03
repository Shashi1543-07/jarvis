import google.generativeai as genai
import os
import json

class LLM:
    def __init__(self):
        self.api_key = self._load_api_key()
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Try different model names in order of preference
            # Using exact names from genai.list_models()
            model_names = [
                'models/gemini-flash-latest',
                'models/gemini-pro-latest'
            ]
            
            self.model = None
            for model_name in model_names:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    self.chat = self.model.start_chat(history=[])
                    print(f"LLM: {model_name} initialized successfully.")
                    break
                except Exception as e:
                    print(f"LLM: Failed to initialize {model_name}: {e}")
                    continue
            
            if not self.model:
                print("LLM: Could not initialize any Gemini model. Intelligence disabled.")
        else:
            self.model = None
            print("LLM: API Key not found. Intelligence disabled.")

    def _load_api_key(self):
        try:
            secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'secrets.json')
            if os.path.exists(secrets_path):
                with open(secrets_path, 'r') as f:
                    secrets = json.load(f)
                    return secrets.get('GEMINI_API_KEY')
        except Exception as e:
            print(f"LLM: Error loading secrets: {e}")
        return None

    def chat_with_context(self, user_input, context, system_instruction=None):
        if not self.model:
            return "I need a Google Gemini API key to think. Please add it to config/secrets.json."

        # Construct a prompt with context
        # We can't easily inject system instructions into an active chat session in the basic API,
        # so we'll prepend it to the user message or use a fresh generation if we want strict system prompting.
        # For a continuous chat, we'll append context.
        
        full_prompt = ""
        if system_instruction:
            full_prompt += f"System: {system_instruction}\n"
        
        full_prompt += f"Context: {context}\n"
        full_prompt += f"User: {user_input}"

        try:
            response = self.chat.send_message(full_prompt)
            return response.text
        except Exception as e:
            print(f"\n❌ LLM Error: {e}")
            return f"I encountered an error thinking: {e}"

    def analyze_image(self, image_path, prompt):
        """Analyze an image using Gemini's vision capabilities"""
        if not self.model:
            return "I need a Google Gemini API key to analyze images. Please add it to config/secrets.json."

        try:
            from PIL import Image
            
            # Load the image
            img = Image.open(image_path)
            
            # Generate content with both text and image
            response = self.model.generate_content([prompt, img])
            return response.text
        except ImportError:
            return "PIL (Pillow) is not installed. Please install it with 'pip install pillow'"
        except Exception as e:
            print(f"\n❌ LLM Vision Error: {e}")
            return f"I encountered an error analyzing the image: {e}"
