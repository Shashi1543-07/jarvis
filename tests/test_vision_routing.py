
import sys
import os

def test_routing():
    print("Testing Vision Routing Logic...")
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jarvis')))
    
    try:
        from actions.vision_actions import _smart_vision_route
        
        test_prompts = [
            "can you even see?",
            "do you see anything?",
            "is there a book?",
            "Read the book header", # The hallucination
            "Read the text on the screen"
        ]
        
        for prompt in test_prompts:
            print(f"\nPrompt: '{prompt}'")
            # We mock the original intent as VISION_OCR to see if smart route intercepts it
            result = _smart_vision_route(prompt, "VISION_OCR")
            
            if result:
                if isinstance(result, dict):
                    print(f"Result Type: {result.get('type')}")
                    print(f"Message: {result.get('message')}")
                else:
                    print(f"Result: {result}")
            else:
                print("Result: None (Passed through to handler)")
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_routing()
