import requests
import json
import time

def diagnose_ollama():
    print("--- Ollama Deep Diagnostic ---")
    base_url = "http://localhost:11434"
    model = "llama3.2:3b"
    
    # 1. Check Tags
    try:
        print(f"1. Checking models at {base_url}/api/tags...")
        res = requests.get(f"{base_url}/api/tags", timeout=10)
        print(f"   Status: {res.status_code}")
        models = [m['name'] for m in res.json().get('models', [])]
        print(f"   Models found: {models}")
        if model not in models and f"{model}:latest" not in models and "llama3.2:latest" not in models:
            print(f"   WARNING: {model} might not be the exact name. Check the list above.")
    except Exception as e:
        print(f"   ERROR: {e}")
        return

    # 2. Test each available model
    print("\n2. Testing generation for each model...")
    for m in models:
        try:
            print(f"   - Testing model '{m}'...")
            payload = {
                "model": m,
                "prompt": "Say 'hello'.",
                "stream": False
            }
            start = time.time()
            res = requests.post(f"{base_url}/api/generate", json=payload, timeout=60)
            duration = time.time() - start
            if res.status_code == 200:
                print(f"     SUCCESS: {m} responded in {duration:.2f}s")
                print(f"     Response: {res.json().get('response')}")
            else:
                print(f"     FAILED: {m} returned {res.status_code}")
        except Exception as e:
            print(f"     TIMEOUT: {m} did not respond within 60s.")

if __name__ == "__main__":
    diagnose_ollama()
