class StepperMotor:
    #CONSTATS
    ROTATION_P_MM = 0.5  # pitch=2mm -> 1/2
    TMC_MICO_STEPPING = 11
    STEPPER_STEPS = 200
    # 2mm * x = Rot / mm
    STEPS_P_ROTATION = TMC_MICO_STEPPING * STEPPER_STEPS  # Step=1.8, when 0.9->400
    STEPS_P_MM = STEPS_P_ROTATION * ROTATION_P_MM  # 900 steps = 1mm

    def __init__(self, name:str, max_pos_mm:float, tmc_mirco_spt:float):
        self.name = name
        self.steps_p_mm = StepperMotor.ROTATION_P_MM * tmc_mirco_spt * StepperMotor.STEPPER_STEPS
        self.max_pos_mm = max_pos_mm # set

        # add stuff to self.reset()
        self.pos_mm = 0. # float


    def __values__(self):
        return {"NAME"    : self.name,
                "pos_mm"  : self.pos_mm,}

    def check_pos(self, difference:float)->bool:
        """check position [mm] = current pos [mm]+ difference [mm] """
        pos = self.pos_mm + difference

        if 0 <= pos <= self.max_pos_mm: # check if the provided pos is in movement range
            return True
        return False

    def reset(self): # use with calibration
        self.pos_mm = 0.

