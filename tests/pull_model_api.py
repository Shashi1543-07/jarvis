import requests
import json
import sys

def pull_model():
    print("--- Pulling llama3.2:3b via API ---")
    url = "http://localhost:11434/api/pull"
    payload = {"name": "llama3.2:3b", "stream": True}
    
    try:
        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()
        
        print("Download started. This may take a few minutes...")
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                status = data.get("status", "")
                completed = data.get("completed", 0)
                total = data.get("total", 0)
                
                if total > 0:
                    percent = (completed / total) * 100
                    print(f"Status: {status} | Progress: {percent:.2f}%", end="\r")
                else:
                    print(f"Status: {status}", end="\r")
                    
                if status == "success":
                    print("\nSUCCESS: Model llama3.2:3b pulled successfully!")
                    return True
    except Exception as e:
        print(f"\nFAILED: {e}")
        return False

if __name__ == "__main__":
    pull_model()
