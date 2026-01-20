import threading
import time
from enum import Enum
from collections import deque
from typing import Callable, Optional, Any
import queue


class VoiceState(Enum):
    """Enhanced voice state enumeration with more granular states"""
    IDLE = "IDLE"
    SLEEP = "SLEEP"
    WAKE_WORD_DETECTED = "WAKE_WORD_DETECTED"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    INTERRUPTED = "INTERRUPTED"
    ERROR = "ERROR"
    INITIALIZING = "INITIALIZING"


class ThreadSafeStateMachine:
    """
    Thread-safe state machine with race condition handling, deadlock prevention,
    and comprehensive state transition management.
    """
    
    def __init__(self):
        # Core state management
        self._state = VoiceState.INITIALIZING
        self._previous_state = VoiceState.INITIALIZING
        self._state_lock = threading.RLock()  # Reentrant lock for recursive calls
        
        # Valid state transitions
        self._valid_transitions = {
            VoiceState.INITIALIZING: [VoiceState.IDLE, VoiceState.SLEEP, VoiceState.ERROR],
            VoiceState.IDLE: [VoiceState.SLEEP, VoiceState.LISTENING, VoiceState.THINKING, VoiceState.ERROR],
            VoiceState.SLEEP: [VoiceState.WAKE_WORD_DETECTED, VoiceState.IDLE, VoiceState.ERROR],
            VoiceState.WAKE_WORD_DETECTED: [VoiceState.LISTENING, VoiceState.ERROR],
            VoiceState.LISTENING: [VoiceState.PROCESSING, VoiceState.THINKING, VoiceState.SPEAKING, 
                                 VoiceState.SLEEP, VoiceState.IDLE, VoiceState.ERROR],
            VoiceState.PROCESSING: [VoiceState.THINKING, VoiceState.SPEAKING, 
                                  VoiceState.LISTENING, VoiceState.IDLE, VoiceState.ERROR],
            VoiceState.THINKING: [VoiceState.SPEAKING, VoiceState.LISTENING, 
                                VoiceState.SLEEP, VoiceState.IDLE, VoiceState.ERROR],
            VoiceState.SPEAKING: [VoiceState.LISTENING, VoiceState.INTERRUPTED, 
                                VoiceState.SLEEP, VoiceState.IDLE, VoiceState.ERROR],
            VoiceState.INTERRUPTED: [VoiceState.LISTENING, VoiceState.ERROR],
            VoiceState.ERROR: [VoiceState.IDLE, VoiceState.SLEEP]
        }
        
        # State transition callbacks
        self._state_callbacks = {}
        self._transition_log = deque(maxlen=100)
        
        # Race condition prevention
        self._transition_in_progress = False
        self._transition_lock = threading.Lock()
        self._transition_timeout = 5.0  # seconds
        
        # State-specific data
        self._state_data = {}
        self._state_timers = {}
        
        # Thread safety for callbacks
        self._callback_lock = threading.Lock()
        
        # Initialize in IDLE state
        self._state = VoiceState.IDLE
        self._log_transition(VoiceState.INITIALIZING, VoiceState.IDLE)
        
        print("ThreadSafeStateMachine initialized and ready")

    def _log_transition(self, from_state: VoiceState, to_state: VoiceState):
        """Log state transition with timestamp"""
        self._transition_log.append({
            'from': from_state,
            'to': to_state,
            'timestamp': time.time(),
            'thread': threading.current_thread().name
        })

    def _validate_transition(self, from_state: VoiceState, to_state: VoiceState) -> bool:
        """Validate if a state transition is allowed"""
        valid_targets = self._valid_transitions.get(from_state, [])
        return to_state in valid_targets

    def set_state(self, new_state: VoiceState, timeout: float = 5.0) -> bool:
        """
        Thread-safe state transition with validation and timeout
        
        Args:
            new_state: Target state to transition to
            timeout: Maximum time to wait for transition
            
        Returns:
            True if transition successful, False otherwise
        """
        start_time = time.time()
        
        # Prevent recursive transitions
        with self._transition_lock:
            if self._transition_in_progress:
                # Check if we've exceeded timeout
                if time.time() - start_time > timeout:
                    print(f"State transition timeout: {self._state} -> {new_state}")
                    return False
                time.sleep(0.001)  # Brief pause to allow other transition to complete
                return self.set_state(new_state, timeout)
            
            self._transition_in_progress = True
        
        try:
            with self._state_lock:
                current_state = self._state
                
                # Validate transition
                if not self._validate_transition(current_state, new_state):
                    print(f"Invalid state transition: {current_state} -> {new_state}")
                    return False
                
                # Store previous state
                self._previous_state = current_state
                
                # Update state
                old_state = self._state
                self._state = new_state
                
                # Record state entry time
                self._state_timers[new_state] = time.time()
                
                # Log transition
                self._log_transition(old_state, new_state)
                
                print(f"State: {old_state.value} -> {new_state.value}")
                
                # Execute callbacks outside the lock to prevent deadlocks
                callbacks_to_execute = []
                with self._callback_lock:
                    if new_state in self._state_callbacks:
                        callbacks_to_execute.append(self._state_callbacks[new_state])
                
                # Execute callbacks after releasing main lock
                for callback in callbacks_to_execute:
                    try:
                        callback(old_state, new_state)
                    except Exception as e:
                        print(f"State callback error: {e}")
                
                return True
                
        finally:
            # Always release the transition lock
            self._transition_in_progress = False

    def get_state(self) -> VoiceState:
        """Thread-safe state retrieval"""
        with self._state_lock:
            return self._state

    def get_previous_state(self) -> VoiceState:
        """Get the previous state"""
        with self._state_lock:
            return self._previous_state

    def is_in_state(self, state: VoiceState) -> bool:
        """Check if currently in a specific state"""
        with self._state_lock:
            return self._state == state

    def get_state_duration(self, state: VoiceState = None) -> float:
        """Get duration in current state (or specified state)"""
        with self._state_lock:
            target_state = state or self._state
            if target_state in self._state_timers:
                return time.time() - self._state_timers[target_state]
            return 0.0

    def register_callback(self, state: VoiceState, callback: Callable[[VoiceState, VoiceState], None]):
        """Register callback for state changes"""
        with self._callback_lock:
            self._state_callbacks[state] = callback

    def unregister_callback(self, state: VoiceState):
        """Remove callback for state changes"""
        with self._callback_lock:
            if state in self._state_callbacks:
                del self._state_callbacks[state]

    def get_transition_history(self, count: int = 10) -> list:
        """Get recent state transitions"""
        with self._state_lock:
            return list(self._transition_log)[-count:]

    def can_transition_to(self, target_state: VoiceState) -> bool:
        """Check if transition to target state is valid from current state"""
        with self._state_lock:
            return self._validate_transition(self._state, target_state)

    def force_state(self, new_state: VoiceState):
        """
        Force state change without validation (use with caution!)
        Useful for error recovery or emergency state changes
        """
        with self._state_lock:
            old_state = self._state
            self._state = new_state
            self._previous_state = old_state
            self._state_timers[new_state] = time.time()
            self._log_transition(old_state, new_state)
            print(f"FORCED State: {old_state.value} -> {new_state.value}")

    def reset_state_timers(self):
        """Reset all state timers"""
        with self._state_lock:
            self._state_timers.clear()
            self._state_timers[self._state] = time.time()


class EnhancedAudioBufferManager:
    """
    Thread-safe audio buffer manager with race condition handling
    """
    
    def __init__(self, max_size: int = 100):
        self.buffers = {}
        self.buffer_locks = {}
        self.max_size = max_size
        self.global_lock = threading.RLock()
        
        # Buffer ownership tracking
        self.buffer_owners = {}  # buffer_id -> thread_id
        self.access_queue = queue.Queue()
        
    def create_buffer(self, buffer_id: str, initial_data=None):
        """Create a new audio buffer"""
        with self.global_lock:
            if buffer_id not in self.buffers:
                self.buffers[buffer_id] = deque(maxlen=self.max_size)
                self.buffer_locks[buffer_id] = threading.RLock()
                if initial_data:
                    self.buffers[buffer_id].append(initial_data)
    
    def write_to_buffer(self, buffer_id: str, data: Any) -> bool:
        """Thread-safe write to buffer with ownership checking"""
        if buffer_id not in self.buffers:
            self.create_buffer(buffer_id)
        
        buffer_lock = self.buffer_locks[buffer_id]
        with buffer_lock:
            current_thread = threading.current_thread().ident
            
            # Check if buffer is owned by another thread
            if buffer_id in self.buffer_owners and self.buffer_owners[buffer_id] != current_thread:
                # Another thread owns this buffer, wait or fail gracefully
                return False
            
            # Take ownership temporarily
            self.buffer_owners[buffer_id] = current_thread
            try:
                self.buffers[buffer_id].append(data)
                return True
            finally:
                # Release ownership
                if self.buffer_owners[buffer_id] == current_thread:
                    del self.buffer_owners[buffer_id]
    
    def read_from_buffer(self, buffer_id: str, count: int = 1) -> list:
        """Thread-safe read from buffer"""
        if buffer_id not in self.buffers:
            return []
        
        buffer_lock = self.buffer_locks[buffer_id]
        with buffer_lock:
            current_thread = threading.current_thread().ident
            
            # Take ownership temporarily
            self.buffer_owners[buffer_id] = current_thread
            try:
                result = []
                for _ in range(min(count, len(self.buffers[buffer_id]))):
                    if self.buffers[buffer_id]:
                        result.append(self.buffers[buffer_id].popleft())
                return result
            finally:
                # Release ownership
                if buffer_id in self.buffer_owners and self.buffer_owners[buffer_id] == current_thread:
                    del self.buffer_owners[buffer_id]
    
    def clear_buffer(self, buffer_id: str):
        """Clear a buffer"""
        if buffer_id in self.buffers:
            buffer_lock = self.buffer_locks[buffer_id]
            with buffer_lock:
                self.buffers[buffer_id].clear()


class RaceConditionSafeVoiceController:
    """
    Main controller that integrates state machine with audio buffer management
    """
    
    def __init__(self):
        self.state_machine = ThreadSafeStateMachine()
        self.buffer_manager = EnhancedAudioBufferManager()
        
        # Thread management
        self.active_threads = {}
        self.thread_lock = threading.Lock()
        
        # Event handling
        self.events = queue.Queue()
        self.event_handlers = {}
        
        print("RaceConditionSafeVoiceController initialized")
    
    def register_thread(self, thread_name: str, thread_obj: threading.Thread):
        """Register an active thread for monitoring"""
        with self.thread_lock:
            self.active_threads[thread_name] = thread_obj
    
    def unregister_thread(self, thread_name: str):
        """Unregister a thread"""
        with self.thread_lock:
            if thread_name in self.active_threads:
                del self.active_threads[thread_name]
    
    def get_active_threads(self) -> dict:
        """Get currently active threads"""
        with self.thread_lock:
            return self.active_threads.copy()
    
    def post_event(self, event_type: str, data: Any = None):
        """Post an event to the event queue"""
        self.events.put({
            'type': event_type,
            'data': data,
            'timestamp': time.time(),
            'thread': threading.current_thread().name
        })
    
    def process_events(self):
        """Process pending events"""
        processed = []
        try:
            while True:
                event = self.events.get_nowait()
                processed.append(event)
                
                # Handle event if handler exists
                if event['type'] in self.event_handlers:
                    handler = self.event_handlers[event['type']]
                    try:
                        handler(event)
                    except Exception as e:
                        print(f"Event handler error: {e}")
        except queue.Empty:
            pass
        
        return processed
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler"""
        self.event_handlers[event_type] = handler
    
    def safe_state_transition(self, new_state: VoiceState, 
                            condition_check: Callable[[], bool] = None,
                            timeout: float = 5.0) -> bool:
        """
        Perform state transition with additional safety checks
        """
        # Check condition if provided
        if condition_check and not condition_check():
            print(f"State transition condition failed: {new_state}")
            return False
        
        # Check if transition is valid
        if not self.state_machine.can_transition_to(new_state):
            print(f"Invalid transition to {new_state} from {self.state_machine.get_state()}")
            return False
        
        # Perform transition
        return self.state_machine.set_state(new_state, timeout)


if __name__ == "__main__":
    # Test the enhanced state machine
    controller = RaceConditionSafeVoiceController()
    
    print("Enhanced state machine with race condition handling initialized")
    print(f"Initial state: {controller.state_machine.get_state().value}")
    
    # Test state transitions
    def test_callback(old_state, new_state):
        print(f"Transition callback executed: {old_state.value} -> {new_state.value}")
    
    controller.state_machine.register_callback(VoiceState.LISTENING, test_callback)
    
    # Perform some safe transitions
    controller.safe_state_transition(VoiceState.SLEEP)
    controller.safe_state_transition(VoiceState.WAKE_WORD_DETECTED)
    controller.safe_state_transition(VoiceState.LISTENING)
    
    print("State machine test completed")