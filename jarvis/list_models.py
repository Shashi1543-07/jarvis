"""
Script to list all available Gemini models for your API key.
"""
import google.generativeai as genai
import os
import json

# Load API key
secrets_path = os.path.join(os.path.dirname(__file__), 'config', 'secrets.json')
with open(secrets_path, 'r') as f:
    secrets = json.load(f)
    api_key = secrets.get('GEMINI_API_KEY')

genai.configure(api_key=api_key)

print("Available Gemini Models:")
print("-" * 50)
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"Model Name: {model.name}")
        print(f"Display Name: {model.display_name}")
        print(f"Supported Methods: {model.supported_generation_methods}")
        print("-" * 50)
