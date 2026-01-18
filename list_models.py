import google.generativeai as genai
import os
import json

def list_gemini_models():
    # Load API Key
    secrets_path = os.path.join(os.getcwd(), 'jarvis', 'config', 'secrets.json')
    with open(secrets_path, 'r') as f:
        secrets = json.load(f)
        api_key = secrets.get('GEMINI_API_KEYS')[0]
    
    genai.configure(api_key=api_key)
    
    print("Listing available models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")

if __name__ == "__main__":
    list_gemini_models()
