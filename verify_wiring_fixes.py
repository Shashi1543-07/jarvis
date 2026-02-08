"""
Quick verification script for Jarvis wiring fixes
Tests the new connectivity and media control patterns
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'jarvis'))

from core.nlu.engine import NLUEngine
from core.nlu.intents import IntentType

def test_wiring_fixes():
    print("=" * 60, flush=True)
    print("JARVIS NLU PATTERN VERIFICATION", flush=True)
    print("=" * 60, flush=True)
    
    nlu = NLUEngine()
    all_passed = True
    
    # Test cases: (input, expected_intent, description)
    test_cases = [
        # WiFi - Critical new patterns
        ("turn on wifi", IntentType.SYSTEM_WIFI_CONNECT, "WiFi: Turn on wifi"),
        ("turn on wi-fi", IntentType.SYSTEM_WIFI_CONNECT, "WiFi: Turn on wi-fi"),
        ("enable wifi", IntentType.SYSTEM_WIFI_CONNECT, "WiFi: Enable"),
        ("connect to wifi", IntentType.SYSTEM_WIFI_CONNECT, "WiFi: Connect"),
        ("turn off wifi", IntentType.SYSTEM_WIFI_DISCONNECT, "WiFi: Turn off"),
        ("disable wifi", IntentType.SYSTEM_WIFI_DISCONNECT, "WiFi: Disable"),
        
        # Bluetooth
        ("turn on bluetooth", IntentType.SYSTEM_BLUETOOTH, "Bluetooth: Turn on"),
        ("enable bluetooth", IntentType.SYSTEM_BLUETOOTH, "Bluetooth: Enable"),
        ("turn off bluetooth", IntentType.SYSTEM_BLUETOOTH, "Bluetooth: Turn off"),
        
        # Hotspot
        ("turn on hotspot", IntentType.SYSTEM_HOTSPOT, "Hotspot: Turn on"),
        ("enable hotspot", IntentType.SYSTEM_HOTSPOT, "Hotspot: Enable"),
        ("start mobile hotspot", IntentType.SYSTEM_HOTSPOT, "Hotspot: Start mobile"),
        ("turn off hotspot", IntentType.SYSTEM_HOTSPOT, "Hotspot: Turn off"),
        
        # Media Control
        ("play music", IntentType.MEDIA_CONTROL, "Media: Play music"),
        ("pause the music", IntentType.MEDIA_CONTROL, "Media: Pause"),
        ("next track", IntentType.MEDIA_CONTROL, "Media: Next"),
        
        # Existing patterns still work
        ("open chrome", IntentType.SYSTEM_OPEN_APP, "System: Open app"),
        ("set volume to 50", IntentType.SYSTEM_CONTROL, "System: Volume"),
    ]
    
    for test_input, expected, description in test_cases:
        intent = nlu.parse(test_input)
        passed = intent.intent_type == expected
        status = "PASS" if passed else "FAIL"
        actual = intent.intent_type.value if hasattr(intent.intent_type, 'value') else str(intent.intent_type)
        expected_val = expected.value if hasattr(expected, 'value') else str(expected)
        
        if not passed:
            all_passed = False
        print(f"[{status}] {description}: '{test_input}' -> {actual}", flush=True)
    
    print("=" * 60, flush=True)
    if all_passed:
        print("ALL TESTS PASSED!", flush=True)
    else:
        print("SOME TESTS FAILED - Review above", flush=True)
    print("=" * 60, flush=True)
    
    return all_passed

if __name__ == "__main__":
    test_wiring_fixes()
