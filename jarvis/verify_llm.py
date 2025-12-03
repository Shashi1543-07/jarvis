"""
Verification script for LLM integration.
This will test if the Gemini API is properly configured.
"""
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.llm import LLM

def test_llm():
    print("Testing LLM Integration...")
    print("-" * 50)
    
    llm = LLM()
    
    if not llm.model:
        print("\n❌ FAILED: API Key not configured.")
        print("\nTo fix this:")
        print("1. Get your free API key from: https://aistudio.google.com/app/apikey")
        print("2. Open: jarvis/config/secrets.json")
        print("3. Replace 'YOUR_API_KEY_HERE' with your actual key")
        return False
    
    print("\n✓ API Key loaded successfully")
    print("\nTesting chat functionality...")
    
    try:
        response = llm.chat_with_context(
            "Hello! Who are you?",
            "",
            "You are Jarvis, an AI assistant."
        )
        
        if "I encountered an error" in response:
            print(f"\n❌ FAILED: The LLM returned an error message.")
            print(f"Response: {response}")
            return False
            
        print(f"\n✓ Response received: {response[:100]}...")
        print("\n✅ SUCCESS: LLM is working!")
        return True
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    test_llm()
