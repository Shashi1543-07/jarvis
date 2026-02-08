import sys
sys.path.insert(0, 'jarvis')
from core.nlu.engine import NLUEngine

engine = NLUEngine()

tests = [
    ("close brave", "SYSTEM_CLOSE_APP"),
    ("remember that my birthday is March 15", "MEMORY_WRITE"),
    ("what do you know about my birthday", "MEMORY_READ"),
    ("recall my name", "MEMORY_READ"),
    ("forget about my email", "MEMORY_FORGET"),
    ("turn on wifi", "SYSTEM_WIFI_CONNECT"),
    ("turn on hotspot", "SYSTEM_HOTSPOT"),
]

print("=" * 50)
print("TESTING NLU + Router Wiring")
print("=" * 50)

for text, expected in tests:
    result = engine.parse(text)
    # Handle different result formats
    if hasattr(result, 'intent'):
        actual = result.intent.value if hasattr(result.intent, 'value') else str(result.intent)
    elif isinstance(result, dict):
        actual = result.get('intent', 'UNKNOWN')
    else:
        actual = str(result)
    status = "PASS" if actual == expected else "FAIL"
    print(f"[{status}] '{text}' -> {actual} (expected: {expected})")

print("=" * 50)
print("ALL TESTS COMPLETE")
