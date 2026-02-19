from MotorOverclass import StepperMotor
from CDC_send import Transmiter, t
import settings

class MotorOutOfRangeError(Exception):#
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class MotorController:
    """control x and y motors with move(x, y) function, use calibrate to reset motor positions to 0, 0
       and move servos
    """
    starting_offsets_user_presets = { # in mm from left bottom corner
        "A4": (40, 40) # measure
    }

    def __init__(self, name="motorController", move_format="A4"):
        self.name = name

        # CDC send instruction object
        self.transmiter = Transmiter()

        #steppermotor objects to store the bullshit motor data
        self.x_motor = StepperMotor(name="x_motor", max_pos_mm=297) # measure
        self.y_motor = StepperMotor(name="y_motor", max_pos_mm=210) # measure

        # deal with starting offset (x, y)
        if move_format in MotorController.starting_offsets_user_presets.keys():# and type(move_format) == str:
            self.starting_offset = MotorController.starting_offsets_user_presets[str(move_format)] # (offset_x, offset_y)
        #else: # user can input custom (offset_x, offset_y)
        #    self.starting_offset = move_format

        #starting sequence
        if not __name__ == "__main__": # when running from this file don't proceed with flowing, running from main:
            # "CALIBRATE" the driver
            self.calibrate()

    def move_to_mm(self, x_target:float, y_target:float)->None:
        """(target - current)(x, y)"""
        
        x_move = x_target - self.x_motor.pos_mm
        y_move = y_target - self.y_motor.pos_mm

        self.mm_move(x=x_move,y=y_move)

    def mm_move(self, x:float, y:float)->None:
        """move by X, Y mm"""

        #check move and add variable position:
        #check x pos
        if self.x_motor.check_pos(x):
            # store to perform subt
            x_motor_move_starting_mmpos = self.x_motor.pos_mm

            self.x_motor.pos_mm += x # update the mm variable in stepper object

            # calculate the steps, based on the position of requried mm pos and current mm pos, due to to rounding errors
            x_steps = round(StepperMotor.STEPS_P_MM * (self.x_motor.pos_mm - x_motor_move_starting_mmpos)) # 10mm*1800steps = 18000 steps

        else:
            raise MotorOutOfRangeError("position: motorX: "  + str(self.x_motor.pos_mm + x))
        # check y pos

        if self.y_motor.check_pos(y):
            # store to perform subt
            y_motor_move_starting_mmpos = self.y_motor.pos_mm

            self.y_motor.pos_mm += y # update the mm variable in stepper object

            # calculate the steps, based on the position of requried mm pos and current mm pos, due to to rounding errors
            y_steps = round(StepperMotor.STEPS_P_MM * (self.y_motor.pos_mm - y_motor_move_starting_mmpos)) # 10mm*1800steps = 18000 steps

        else:
            raise MotorOutOfRangeError("position: motorY: "  + str(self.y_motor.pos_mm + y))

        # x or y may be undefinned, but if they are, Motor error will be raised
        
        self.step_move(x=x_steps, y=y_steps)


    def step_move(self, x:int, y:int)->None:
        print(f"{t()}: requesting: Move, steps: x: {x} y: {y}")

        if not settings.TEST_MODE:

            recive_state = self.transmiter.send_and_receive("MOV " + str(x) + " " + str(y) + "\n")
            print(f"{t()}: Move: {recive_state=}")

            finish_state = self.transmiter.send_and_receive(None) # wait for finish
            print(f"{t()}: Move: {finish_state=}\n")



    def calibrate(self)->None:
        # send calibrate instruction
        print(f"{t()}: requesting: Calibrate")

        if not settings.TEST_MODE:
            recive_state = self.transmiter.send_and_receive("CLB\n")
            print(f"{t()}: Calibrate: {recive_state=}")

            finish_state = self.transmiter.send_and_receive(None) # wait for finish
            print(f"{t()}: Calibrate: {finish_state=}\n")

        # reset the motors
        self.x_motor.reset()
        self.y_motor.reset()

        #reset the servo as well?

    def penUp(self):

        print(f"{t()}: requesting: penUp")
        
        if not settings.TEST_MODE:
            recive_state = self.transmiter.send_and_receive("PUP\n")
            print(f"{t()}: penUp: {recive_state=}")

            finish_state = self.transmiter.send_and_receive(None) # wait for finish
            print(f"{t()}: penUp: {finish_state=}\n")

    def penDown(self):

        print(f"{t()}: requesting: penDown")
        
        if not settings.TEST_MODE:
            recive_state = self.transmiter.send_and_receive("PDN\n")    
            print(f"{t()}: penDown ret: {recive_state=}")

            finish_state = self.transmiter.send_and_receive(None) # wait for finish
            print(f"{t()}: penDown: {finish_state=}\n")
