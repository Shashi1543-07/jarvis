from jarvis.core.nlu.intents import Intent, IntentType
from jarvis.actions.system_actions import handle_system_control
import re

def test_brightness_dispatch():
    print("Testing brightness dispatch logic...")
    
    # Simulate what NLUEngine and Router would do now
    test_cases = [
        {
            "original_text": "increase the screen brightness to 100%",
            "slots": {"command": "increase brightness"} # Old NLU might just give this
        },
        {
            "original_text": "set brightness to 50%",
            "slots": {"command": "set brightness to 50%"} # New NLU should give this
        },
        {
            "original_text": "increase brightness by 20%",
            "slots": {"command": "increase brightness"}
        },
        {
            "original_text": "dim the screen by 30",
            "slots": {"command": "decrease brightness"}
        }
    ]

    for case in test_cases:
        print(f"\nInput: {case['original_text']}")
        # In Router._execute_intent, we now do:
        kwargs = {**case['slots'], "text": case['original_text']}
        
        # In system_actions.handle_system_control:
        cmd = (kwargs.get("command") or "").lower()
        content = kwargs.get("content", "")
        text = kwargs.get("text", "")
        
        all_text = f"{cmd} {content} {text}".lower()
        nums = re.findall(r'(\d+)', all_text)
        
        print(f"  Extracted nums: {nums}")
        print(f"  all_text sample: {all_text[:50]}...")
        
        if nums:
            val = int(nums[0])
            if "to" in all_text or "set" in all_text or "at" in all_text:
                print(f"  Result: would call set_brightness({val})")
            elif "increase" in all_text or "up" in all_text:
                print(f"  Result: would call increase_brightness({val})")
            elif "decrease" in all_text or "down" in all_text:
                print(f"  Result: would call decrease_brightness({val})")
            else:
                print(f"  Result: would call set_brightness({val}) (default)")
        else:
            if "increase" in cmd:
                print("  Result: would call increase_brightness() (default step)")
            elif "decrease" in cmd:
                print("  Result: would call decrease_brightness() (default step)")
            else:
                print("  Result: would call adjust_brightness()")

if __name__ == "__main__":
    test_brightness_dispatch()
