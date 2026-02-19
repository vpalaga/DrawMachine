from segmentFunctions import Instruction

class FCODE:
    paper_sizes = {  # in mm
        "A4": (297, 210)
    }
    def __init__(self, size: tuple[float, float]|str, name:str):

        if type(size) == str: # convert from str type to x_mm, y_mm
            if size in FCODE.paper_sizes.keys():
                size = FCODE.paper_sizes[size]
            else:
                raise KeyError("Paper size: {" + size + "} is invalid")

        self.name = name
        self.header = {
            "header_length": -1,
            "name": name,
            "plane_size_mm": (size[0], size[1])
        }

        self.header["header_length"] = len(self.header.keys())
        self.instructions:list[Instruction] = []


    def add_instruction(self, instruction: Instruction):
        self.instructions.append(instruction)


    def save(self):
        with open(self.header["name"] + ".FCODE", "w") as file:
            for (k,v) in self.header.items():
                file.write(k + " " + str(v) + "\n")

            for instruction in self.instructions:
                file.write(instruction.self_str() + "\n")




