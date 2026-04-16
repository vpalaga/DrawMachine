from MotorOverclass import StepperMotor
from CDC_send import Transmitter, t
import settings

class MotorOutOfRangeError(Exception):#
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class MotorController:
    """control x and y motors with the move (x, y) function, use calibrating to reset motor positions to 0, 0
       and move servos
    """
    starting_offsets_user_presets = { # in mm from left bottom corner
        "A4": (25, 37) # measure
    }

    def __init__(self, name="motorController", move_format="A4"):
        self.name = name

        # CDC send instruction object
        self.transmitter = Transmitter(console=False)

        #stepper motor objects to store the bullshit motor data
        self.x_motor = StepperMotor(name="x_motor", max_pos_mm=297) # measure
        self.y_motor = StepperMotor(name="y_motor", max_pos_mm=210) # measure

        # deal with starting offset (x, y)
        if move_format in MotorController.starting_offsets_user_presets.keys():# and type(move_format) == str:
            self.starting_offset = MotorController.starting_offsets_user_presets[str(move_format)] # (offset_x, offset_y)
        #else: # user can input custom (offset_x, offset_y)
        #    self.starting_offset = move_format

        # move to the starting position
        self.mm_move(*self.starting_offset)
        # reset positon to 0,0
        self.x_motor.reset()
        self.y_motor.reset()

    def move_to_mm(self, x_target:float, y_target:float)->None:
        """(target - current) (x, y)"""
        
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

            # calculate the steps, based on the position of required mm pos and current mm pos, due to rounding errors
            x_steps = round(StepperMotor.STEPS_P_MM * (self.x_motor.pos_mm - x_motor_move_starting_mmpos)) # 10mm*1800steps = 18000 steps

        else:
            raise MotorOutOfRangeError("position: motor X: "  + str(self.x_motor.pos_mm + x))
        # check y pos

        if self.y_motor.check_pos(y):
            # store to perform subt
            y_motor_move_starting_mmpos = self.y_motor.pos_mm

            self.y_motor.pos_mm += y # update the mm variable in stepper object

            # calculate the steps, based on the position of required mm pos and current mm pos, due to rounding errors
            y_steps = round(StepperMotor.STEPS_P_MM * (self.y_motor.pos_mm - y_motor_move_starting_mmpos)) # 10mm*1800steps = 18000 steps

        else:
            raise MotorOutOfRangeError("position: motor Y: "  + str(self.y_motor.pos_mm + y))

        # x or y may be undefined, but if they are, Motor error will be raised
        
        self.step_move(x=x_steps, y=y_steps)

    def step_move(self, x:int, y:int)->None:
        print(f"{t()}: requesting: Move, steps: x: {x} y: {y} estimated time: {max(x, y)/5000}s")

        if not settings.TEST_MODE:

            receive_state = self.transmitter.send_and_receive("MOV " + str(x) + " " + str(y) + "\n")
            print(f"{t()}: Move: {receive_state=}")

            finish_state = self.transmitter.send_and_receive(None) # wait for finish
            print(f"{t()}: Move: {finish_state=}\n")

    def calibrate(self)->None:
        # send calibrate instruction
        print(f"{t()}: requesting: Calibrate")

        if not settings.TEST_MODE:
            receive_state = self.transmitter.send_and_receive("CLB\n")
            print(f"{t()}: Calibrate: {receive_state=}")

            finish_state = self.transmitter.send_and_receive(None) # wait for finish
            print(f"{t()}: Calibrate: {finish_state=}\n")

            # move to starting offset
            self.move_to_mm(*MotorController.starting_offsets_user_presets["A4"])

        # reset the motors
        self.x_motor.reset()
        self.y_motor.reset()

        #reset the servo as well?

    def penUp(self):

        print(f"{t()}: requesting: penUp")
        
        if not settings.TEST_MODE:
            receive_state = self.transmitter.send_and_receive("SCA 0 30P\n")
            print(f"{t()}: penUp: {receive_state=}")

            finish_state = self.transmitter.send_and_receive(None) # wait for finish
            print(f"{t()}: penUp: {finish_state=}\n")

    def penDown(self):

        print(f"{t()}: requesting: penDown")
        
        if not settings.TEST_MODE:
            receive_state = self.transmitter.send_and_receive("SCA 0 0\n")
            print(f"{t()}: penDown ret: {receive_state=}")

            finish_state = self.transmitter.send_and_receive(None) # wait for finish
            print(f"{t()}: penDown: {finish_state=}\n")

    def wait(self, secs):
        print(f"{t()}: requesting: wait")
        
        receive_state = self.transmitter.send_and_receive("WAT " + secs + "\n")
        print(f"{t()}: wait ret: {receive_state=}")

        finish_state = self.transmitter.send_and_receive(None) # wait for finish
        print(f"{t()}: wait: {finish_state=}\n")
            
