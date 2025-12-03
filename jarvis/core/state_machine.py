class StateMachine:
    def __init__(self):
        self.state = "IDLE"
        self.on_state_change = None

    def set_state(self, new_state):
        if self.state != new_state:
            print(f"State Transition: {self.state} -> {new_state}")
            self.state = new_state
            if self.on_state_change:
                self.on_state_change(new_state)

    def get_state(self):
        return self.state
