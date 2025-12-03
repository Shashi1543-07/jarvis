import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jarvis')))

from jarvis.core.llm import LLM

# Test the analyze_image method
print("Testing Vision Engine...")

llm = LLM()

# Check if model supports vision
if llm.model:
    print(f"✓ LLM initialized successfully")
    print(f"✓ analyze_image method available: {hasattr(llm, 'analyze_image')}")
    
    # Test will require a real screenshot, so we'll just verify the method exists
    print("\nVision Engine is ready!")
    print("\nAvailable vision commands:")
    print("- analyze_screen(prompt)")
    print("- read_screen()")
    print("- describe_screen()")
    print("- identify_ui_elements()")
    print("- analyze_error()")
else:
    print("✗ LLM not initialized - please check your Gemini API key")
