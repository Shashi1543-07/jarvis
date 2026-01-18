import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'jarvis'))

from core.llm import LLM

def test_llm_vision():
    print("Initializing LLM...")
    llm = LLM()
    
    image_path = "C:/Users/lenovo/.gemini/antigravity/brain/0381e249-26ce-446b-ab19-44231883f54c/uploaded_image_1768724284980.png"
    
    if not os.path.exists(image_path):
        print(f"Image not found at {image_path}")
        return

    print(f"Testing Vision with model: {llm.model_name}")
    print("Analyzing image...")
    
    try:
        result = llm.analyze_image(image_path, "Describe this image briefly.")
        print("Result:", result)
        
        if "error" in result.lower() and ("quota" in result.lower() or "404" in result.lower()):
            print("❌ LLM Vision Failed")
        else:
            print("✅ LLM Vision Passed")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_llm_vision()
