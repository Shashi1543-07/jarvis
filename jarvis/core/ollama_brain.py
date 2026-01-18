import requests
import json
import time

class OllamaBrain:
    """Interface to local Ollama LLM for reasoning and chat."""
    
    def __init__(self, model="gemma3:1b", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.generate_url = f"{base_url}/api/generate"
        print(f"OllamaBrain initialized with model: {self.model}")

    def chat_with_context(self, user_input, context, system_instruction=None):
        """
        Send a message to Ollama using generate endpoint for maximum compatibility.
        """
        prompt = ""
        if system_instruction:
            prompt += f"System: {system_instruction}\n"
        if context:
            prompt += f"Context: {context}\n"
        prompt += f"User: {user_input}\nAssistant:"

        print(f"DEBUG: Calling Ollama Generate ({self.generate_url}) for model: {self.model}...")
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        
        try:
            start_time = time.time()
            response = requests.post(self.generate_url, json=payload, timeout=90)
            print(f"DEBUG: Ollama responded in {time.time() - start_time:.2f}s with status {response.status_code}")
            response.raise_for_status()
            result = response.json()
            return result.get("response", "Error: No response content from Ollama.")
        except requests.exceptions.ConnectionError:
            print("ERROR: Ollama connection failed. Is the server running?")
            return "ERROR_CONNECTION"
        except requests.exceptions.ReadTimeout:
            print("ERROR: Ollama ReadTimeout (90s). System is likely too slow for this model.")
            return "ERROR_TIMEOUT"
        except Exception as e:
            print(f"ERROR: Ollama Exception: {e}")
            return f"ERROR_OTHER: {str(e)}"

    def generate_response(self, prompt, system=None):
        """Simple generation without history."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False
        }
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            return f"Ollama Gen Error: {str(e)}"

    def check_health(self):
        """Verify Ollama is reachable."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def generate_research_report(self, research_prompt):
        """Generates a structured research report based on scraped data."""
        system_instruction = (
            "You are JARVIS, a sophisticated AI assistant. "
            "Your goal is to provide a high-level research synthesis based on the provided sources. "
            "Maintain an elegant, helpful, and slightly formal tone. "
            "Use markdown for structure. Always cite sources as [Source X]."
        )
        return self.chat_with_context(research_prompt, context=None, system_instruction=system_instruction)
