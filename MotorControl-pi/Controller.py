from MotorController import MotorController

class Controller():
    
    def __init__(self, file_path:str):
        self.file_path:str = file_path
        self.motor_driver:MotorController = MotorController()

        self.instructions = open(file_path,"r").readlines()

    def do_file(self):
        # skip header
        header_size:int = int(self.instructions[0].split(" ")[1]) # first line, second block after " ", convert to int 
        print(f"{header_size=}")

        for line in self.instructions[header_size:]: # skip from after the header
            current_istruction:list[str] = line.split(" ")
            
            instruction_type:str = current_istruction[0]
            
            match instruction_type:
                case "MOV":
                    # pass the x and y argument
                    self.motor_driver.move_to_mm(float(current_istruction[1]), float(current_istruction[2]))
                case "CLB":
                    self.motor_driver.calibrate()
                case "PUP":
                    self.motor_driver.penUp()
                case "PDN": 
                    self.motor_driver.penDown()