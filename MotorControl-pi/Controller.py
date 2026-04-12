from MotorController import MotorController

class Controller:
    
    def __init__(self, file_path:str):
        self.file_path:str = file_path
        self.motor_driver:MotorController = MotorController()

        self.instructions = open(file_path,"r").readlines()

    def do_file(self):
        # skip header
        header_size:int = int(self.instructions[0].split(" ")[1]) # first line, second block after " ", convert to int 
        print(f"{header_size=}")
        
        instructions_len = len(self.instructions[header_size:])
        instructions_len_string_len = len(str(instructions_len))

        for i, line in enumerate(self.instructions[header_size:]): # skip from after the header
            current_instruction:list[str] = line.split(" ")
            
            instruction_type:str = current_instruction[0]
            print(f"Instruction: {i:>{instructions_len_string_len}}/{instructions_len}")

            match instruction_type:
                case "MOV":
                    # pass the x and y argument
                    self.motor_driver.move_to_mm(float(current_instruction[1]), float(current_instruction[2]))
                case "CLB":
                    self.motor_driver.calibrate()
                case "PUP":
                    self.motor_driver.penUp()
                case "PDN": 
                    self.motor_driver.penDown()
                case "WAT":
                    self.motor_driver.wait(float(current_instruction[0]))