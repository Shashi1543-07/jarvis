import google.generativeai as genai
import json
import os

def check_keys():
    secrets_path = os.path.join(os.path.dirname(__file__), 'jarvis', 'config', 'secrets.json')
    if not os.path.exists(secrets_path):
        print("Secrets file not found.")
        return

    with open(secrets_path, 'r') as f:
        secrets = json.load(f)
        keys = secrets.get('GEMINI_API_KEYS', [])

    for i, key in enumerate(keys):
        print(f"\n--- Checking Key {i+1}: {key[:10]}... ---")
        try:
            genai.configure(api_key=key, transport='rest')
            print("Successfully configured client.")
            
            models = genai.list_models()
            print("Successfully listed models. RAW NAMES:")
            for m in models:
                print(f" - {m.name}")
            
            # Try a very small request to test quota on a known good model
            print("\nAttempting test request on gemini-pro...")
            try:
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content("ping", generation_config={"max_output_tokens": 5})
                print(f"Test Success (pro): {response.text}")
            except Exception as test_e:
                print(f"Test Failed (pro): {test_e}")
                
        except Exception as e:
            print(f"Error checking key {i+1}: {e}")

if __name__ == "__main__":
    check_keys()
