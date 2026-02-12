from MotorOverclass import StepperMotor
from SwitchHandler import SwitchOverclass

class MotorController:
    """control x and y motors simultaneously with move(x, y) function, use calibrate to reset motor positions to 0, 0"""
    starting_offsets_user_presets = { # in mm from left bottom corner
        "A4": (40, 40) # measure
    }

    def __init__(self, name="motorController", move_format="A4"|tuple[float,float]):
        self.name = name

        self.x_motor = StepperMotor(name="x_motor", max_pos_mm=270) # measure
        self.y_motor = StepperMotor(name="y_motor", max_pos_mm=210) # measure

        self.switches = SwitchOverclass()

        # deal with starting offset (x, y)
        if move_format in MotorController.starting_offsets_user_presets.keys():# and type(move_format) == str:
            self.starting_offset = MotorController.starting_offsets_user_presets[str(move_format)] # (offset_x, offset_y)
        #else: # user can input custom (offset_x, offset_y)
        #    self.starting_offset = move_format

        #starting sequence
        if not __name__ == "__main__": # when running from this file don't proceed with flowing, running from main:
            self.calibrate()



    def calibrate(self) -> None:
        """move to absolute right bottom corner: |_"""
        x_switch, y_switch = self.switches.get_states()
        x, y = -1, -1
        while not (x_switch and y_switch): # repeat until both switches are conducting [logic tested 27.12.25]
            if x_switch:
                x = 0
            if y_switch:
                y = 0

            self.step_move(x, y) # calibration might go below 0

            x_switch, y_switch = self.switches.get_states()

        self.x_motor.reset()
        self.y_motor.reset()

        #deal with starting offset
        self.mm_move(x=self.starting_offset[0], y=self.starting_offset[1])


    def move_to_mm(self, x_target:float, y_target:float)->None:
        """(target - current)(x, y)"""
        x_move, y_move = x_target - self.x_motor.pos_mm, y_target - self.y_motor.pos_mm
        self.mm_move(x=x_move,y=y_move)

    def mm_move(self, x:float, y:float)->None:
        """move by X, Y mm"""
        x_steps, y_steps = int(x // StepperMotor.STEP_IN_MM), int(y // StepperMotor.STEP_IN_MM) # 10/0.01= 10*100= 1000steps

        #check move and add variable position:
        #check x pos
        if x != 0:
            if self.x_motor.check_pos(x):
                self.x_motor.pos_mm += x_steps * StepperMotor.STEP_IN_MM # get the position back due to rounding errors  # 0.001cm [0.01mm]

                self.x_motor.pos_step += x_steps
                self.x_motor.rotation += x * StepperMotor.ROTATION_P_MM # 1MM->0.5 Rot, 2mm -> 1Rot

            else:
                raise ValueError("position: motorX" + str(self.x_motor.pos_mm + x))
        # check y pos
        if y != 0:
            if self.y_motor.check_pos(y):
                self.y_motor.pos_mm += y_steps * StepperMotor.STEP_IN_MM  # 0.001cm [0.01mm]

                self.y_motor.pos_step += y_steps
                self.y_motor.rotation += y * StepperMotor.ROTATION_P_MM # 1MM->0.5 Rot, 2mm -> 1Rot

            else:
                raise ValueError("position: motorY" + str(self.y_motor.pos_mm + y))

        self.step_move(x=x_steps, y=y_steps)


    def step_move(self, x:int, y:int)->None:
        """move by x, y steps in positive or negative direction"""


        # do the low level stuff here
