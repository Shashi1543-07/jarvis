from enum import Enum, auto
import threading
from typing import Set

class PermissionLevel(Enum):
    READ_ONLY = auto()      # Read state only (default)
    SYSTEM_CONTROL = auto() # Open/Close apps, Volume
    INPUT_EMULATION = auto() # Mouse/Keyboard
    DESTRUCTIVE = auto()    # Delete files, Shutdown

class EmergencyStop:
    """
    Global emergency stop signal.
    """
    _stop_event = threading.Event()
    
    @classmethod
    def trigger(cls):
        print("!!! EMERGENCY STOP TRIGGERED !!!")
        cls._stop_event.set()
        
    @classmethod
    def reset(cls):
        cls._stop_event.clear()
        
    @classmethod
    def is_set(cls):
        return cls._stop_event.is_set()

class PermissionGate:
    """
    Manages active permissions for the Executor.
    """
    def __init__(self):
        # Default permissions for now. In real app, user sets these.
        self.active_permissions: Set[PermissionLevel] = {
            PermissionLevel.READ_ONLY,
            PermissionLevel.SYSTEM_CONTROL, 
            PermissionLevel.INPUT_EMULATION 
            # DESTRUCTIVE not granted by default
        }

    def check_permission(self, level: PermissionLevel) -> bool:
        if level in self.active_permissions:
            return True
        print(f"Permission Denied: Required {level.name}")
        return False

    def grant(self, level: PermissionLevel):
        self.active_permissions.add(level)
        print(f"Permission Granted: {level.name}")

    def revoke(self, level: PermissionLevel):
        if level in self.active_permissions:
            self.active_permissions.remove(level)
            print(f"Permission Revoked: {level.name}")
