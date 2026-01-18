import requests
import sys
import os

# Add the project root to path to import core modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'jarvis'))

def check_ollama():
    print("--- Ollama Connectivity Check ---")
    base_url = "http://localhost:11434"
    
    try:
        # 1. Check if Ollama is running
        print(f"Checking {base_url}...")
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            print("SUCCESS: Ollama server is running.")
            models = response.json().get("models", [])
            if models:
                print("Available models:")
                for m in models:
                    print(f" - {m['name']}")
            else:
                print("WARNING: No models found. Use 'ollama pull llama3.2:3b' to download a model.")
        else:
            print(f"FAILED: Server returned status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("FAILED: Could not connect to Ollama. Please ensure Ollama is installed and running.")
        print("Download at: https://ollama.com/")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    check_ollama()
