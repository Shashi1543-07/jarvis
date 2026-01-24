import re

def handle_brightness_logic(cmd, slots, original_text):
    kwargs = {**slots, "text": original_text}
    
    cmd = (kwargs.get("command") or "").lower()
    content = kwargs.get("content", "")
    text = kwargs.get("text", "")
    
    all_text = f"{cmd} {content} {text}".lower()
    nums = re.findall(r'(\d+)', all_text)
    
    print(f"Extracted nums: {nums}")
    
    if nums:
       val = int(nums[0])
       if "to" in all_text or "set" in all_text or "at" in all_text:
           return f"set_brightness({val})"
       elif "increase" in all_text or "up" in all_text:
           return f"increase_brightness({val})"
       elif "decrease" in all_text or "down" in all_text:
           return f"decrease_brightness({val})"
       return f"set_brightness({val}) (default)"
    elif "increase" in cmd:
       return "increase_brightness() (default)"
    elif "decrease" in cmd:
       return "decrease_brightness() (default)"
    return "adjust_brightness()"

test_cases = [
    ("increase brightness", {"command": "increase brightness"}, "increase the screen brightness to 100%"),
    ("set brightness to 50%", {"command": "set brightness to 50%"}, "set brightness to 50%"),
    ("mute", {"command": "mute"}, "mute the voice"),
    ("unmute", {"command": "unmute"}, "unmute"),
    ("volume_decrease", {"command": "volume_decrease"}, "decrease the volume to 50%"),
    ("dim the screen by 30", {"command": "decrease brightness"}, "dim the screen by 30")
]

for cmd, slots, text in test_cases:
    result = handle_brightness_logic(cmd, slots, text)
    print(f"Input: {text}")
    print(f"  Result: {result}")
    print("-" * 20)
