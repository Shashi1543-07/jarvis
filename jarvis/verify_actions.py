import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_actions():
    print("Verifying Action Modules...")
    print("-" * 50)
    
    try:
        from actions import (
            system_actions,
            web_actions,
            media_actions,
            file_actions,
            app_actions,
            input_actions,
            productivity_actions,
            info_actions,
            comms_actions,
            ai_actions,
            memory_actions,
            vision_actions
        )
        print("✅ All action modules imported successfully.")
    except ImportError as e:
        print(f"❌ Failed to import action modules: {e}")
        return

    print("\nTesting specific actions...")
    
    # Test system_actions
    try:
        print(f"Time: {system_actions.check_time()}")
        print("✅ system_actions.check_time() passed")
    except Exception as e:
        print(f"❌ system_actions failed: {e}")

    # Test file_actions
    try:
        res = file_actions.create_file("test_note.txt", "This is a test.")
        print(f"File Create: {res}")
        res = file_actions.read_file("test_note.txt")
        print(f"File Read: {res}")
        file_actions.delete_file("test_note.txt")
        print("✅ file_actions passed")
    except Exception as e:
        print(f"❌ file_actions failed: {e}")

    # Test math
    try:
        res = ai_actions.solve_math("2 + 2")
        print(f"Math: {res}")
        print("✅ ai_actions.solve_math() passed")
    except Exception as e:
        print(f"❌ ai_actions failed: {e}")

    print("-" * 50)
    print("Verification Complete.")

if __name__ == "__main__":
    test_actions()
