from MotorOverclass import StepperMotor
from CDC_send import Transmitter
from idkfornow import RequestReport, RequestFailCheck
import settings

class MotorOutOfRangeError(Exception):#
    def __init__(self, motor:StepperMotor, difference:float|int):
        self.message = f"{motor.name} out of range: from'{motor.pos_mm}' to '{motor.pos_mm+difference}"
        super().__init__(self.message)

class MotorController:
    """control x and y motors with the move (x, y) function, use calibrating to reset motor positions to 0, 0
       and move servos
    """
    starting_offsets_user_presets = { # in mm from left bottom corner
        "A4": (45, 40) # measure
    }

    def __init__(self, move_format="A4"):

        # CDC send instruction object
        self.transmitter = Transmitter(console=False)

        #stepper motor objects to store the bullshit motor data
        self.x_motor = StepperMotor(name="x_motor", max_pos_mm=297, tmc_mirco_spt=16) # measure
        self.y_motor = StepperMotor(name="y_motor", max_pos_mm=210, tmc_mirco_spt=16) # measure

        # deal with starting offset (x, y)
        if move_format in MotorController.starting_offsets_user_presets.keys():# and type(move_format) == str:
            self.starting_offset = MotorController.starting_offsets_user_presets[str(move_format)] # (offset_x, offset_y)
        #else: # user can input custom (offset_x, offset_y)
        #    self.starting_offset = move_format

        # calib
        self.calibrate()

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
            x_steps = round(self.x_motor.steps_p_mm * (self.x_motor.pos_mm - x_motor_move_starting_mmpos)) # 10mm*1800steps = 18000 steps

        else:
            raise MotorOutOfRangeError(self.x_motor, x)
        # check y pos

        if self.y_motor.check_pos(y):
            # store to perform subt
            y_motor_move_starting_mmpos = self.y_motor.pos_mm

            self.y_motor.pos_mm += y # update the mm variable in stepper object

            # calculate the steps, based on the position of required mm pos and current mm pos, due to rounding errors
            y_steps = round(self.y_motor.steps_p_mm * (self.y_motor.pos_mm - y_motor_move_starting_mmpos)) # 10mm*1800steps = 18000 steps

        else:
            raise MotorOutOfRangeError(self.y_motor, y)

        # x or y may be undefined, but if they are, Motor error will be raised
        
        self.step_move(x=x_steps, y=y_steps)

    @RequestReport
    def step_move(self, x:int, y:int)->None:
        if not settings.TEST_MODE:
            receive_state = self.transmitter.send_and_receive("MOV " + str(x) + " " + str(y) + "\n")
            finish_state = self.transmitter.send_and_receive(None) # wait for finish
            RequestFailCheck(receive_state, finish_state)

    @RequestReport
    def calibrate(self)->None:
        # send calibrate instruction

        if not settings.TEST_MODE:
            receive_state = self.transmitter.send_and_receive("CLB\n")
            finish_state = self.transmitter.send_and_receive(None) # wait for finish
            RequestFailCheck(receive_state, finish_state)

            # move to starting offset
            self.move_to_mm(*MotorController.starting_offsets_user_presets["A4"])

        # reset the motors
        self.x_motor.reset()
        self.y_motor.reset()

        #reset the servo as well?

    @RequestReport
    def penUp(self):
        if not settings.TEST_MODE:
            receive_state = self.transmitter.send_and_receive("SCA 0 30P\n")
            finish_state = self.transmitter.send_and_receive(None) # wait for finish
            RequestFailCheck(receive_state, finish_state)

    @RequestReport
    def penDown(self):
        if not settings.TEST_MODE:
            receive_state = self.transmitter.send_and_receive("SCA 0 0\n")
            finish_state = self.transmitter.send_and_receive(None) # wait for finish
            RequestFailCheck(receive_state, finish_state)

    @RequestReport
    def wait(self, secs):
        receive_state = self.transmitter.send_and_receive("WAT " + secs + "\n")
        finish_state = self.transmitter.send_and_receive(None) # wait for finish
        RequestFailCheck(receive_state, finish_state)