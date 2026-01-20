import sys
import os
import time

# Ensure the project root is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.voice.state_machine_enhanced import VoiceState, RaceConditionSafeVoiceController

def test_state_recovery():
    print("Testing State Recovery...")
    controller = RaceConditionSafeVoiceController()
    sm = controller.state_machine
    
    # Test valid recovery to IDLE
    sm.force_state(VoiceState.LISTENING)
    print(f"Current: {sm.get_state()}")
    
    success = sm.set_state(VoiceState.IDLE)
    print(f"Transition LISTENING -> IDLE: {success}")
    if not success: return False
    
    sm.force_state(VoiceState.THINKING)
    success = sm.set_state(VoiceState.IDLE)
    print(f"Transition THINKING -> IDLE: {success}")
    if not success: return False
    
    sm.force_state(VoiceState.IDLE)
    success = sm.set_state(VoiceState.THINKING)
    print(f"Transition IDLE -> THINKING: {success}")
    if not success: return False
    
    print("State Machine Recovery Test: PASSED")
    return True

if __name__ == "__main__":
    if test_state_recovery():
        print("\nALL SYSTEMS GO. The state machine is now robust.")
        sys.exit(0)
    else:
        print("\nFAILURE. State transitions are still too restrictive.")
        sys.exit(1)
