class SwitchOverclass:
    """connect the switches to raspberry pi main (NOT microcontroller!)"""
    def __init__(self):
        self.x_start_switch = Switch("x")
        self.y_start_switch = Switch("y")

    def get_states(self) -> tuple[bool, bool]:
        return self.x_start_switch.get_state(), self.y_start_switch.get_state()

class Switch:
    def __init__(self, name: str):
        self.name = name

    def get_state(self) -> bool:
        """False = Off, True = On"""
        # low lever stuff
        print("getting state for: " + self.name) # rf later
        state = False
        return state