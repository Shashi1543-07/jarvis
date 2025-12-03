import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.router import Router

# Mock Brain to return a combo action without calling LLM
class MockBrain:
    def think(self, text, short_term, long_term):
        # Simulate a response for "Create a file named combo_test.txt and write 'Success' in it"
        return json.dumps({
            "intent": "combo",
            "reply": "Creating file and writing content.",
            "steps": [
                {
                    "intent": "create_file",
                    "parameters": {
                        "file_path": "combo_test.txt",
                        "content": ""
                    }
                },
                {
                    "intent": "write_file",
                    "parameters": {
                        "file_path": "combo_test.txt",
                        "content": "Success"
                    }
                }
            ]
        })

def test_combo():
    print("Testing Combo Logic...")
    print("-" * 50)
    
    router = Router()
    # Inject mock brain
    router.brain = MockBrain()
    
    response = router.route("Do the combo test")
    
    print(f"Response Intent: {response['intent']}")
    print(f"Results: {response.get('results')}")
    
    # Verify file creation
    if os.path.exists("combo_test.txt"):
        with open("combo_test.txt", "r") as f:
            content = f.read()
        print(f"File Content: {content}")
        if content == "Success":
            print("✅ Combo test passed: File created and written to.")
        else:
            print("❌ Combo test failed: Content mismatch.")
        
        # Cleanup
        os.remove("combo_test.txt")
    else:
        print("❌ Combo test failed: File not created.")

if __name__ == "__main__":
    test_combo()
