import math

class Instruction:
    instructions_parameters_len = { # check if the parameters are correct
        "MOV": 2,
        "PUP": 0,
        "PDN": 0,
        "WAT": 1,
        "CLB": 0}

    def __init__(self, i_type:str, *args:int|float, acc=0.01):
        self.i_type = i_type.upper()  # instruction type

        self.round_up_to = round(-math.log(acc, 10)) # ndigits from decimals 0.001 -> 3
        self.parameters = [float(round(p, ndigits=self.round_up_to)) for p in args] # instructions parameters turn into floats

        # handle warnings and formating Errors
        if self.i_type not in Instruction.instructions_parameters_len.keys(): # check if the instruction is known
            raise Warning("instruction: " + self.i_type + " is unknown")

        if len(self.parameters) != Instruction.instructions_parameters_len[self.i_type]: # check if the right amount of parameters provided
            raise ValueError("for instruction: " + self.i_type +
                             " parameters: "  + str(self.parameters) +
                             " don't match expected length: " + str(Instruction.instructions_parameters_len[self.i_type]))

    def self_str(self): # return string ready for FCODE file writing
        return self.i_type + " " + str(self.parameters).strip("[]").replace(",","")

if __name__ == "__main__":
    print(Instruction( "ove", 20.05, 25).self_str())