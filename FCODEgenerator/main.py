from dxfReader import Reader
from gen import FCODE
from imageHandler import Visual
from segmentFunctions import Instruction

class FGenerator:
    def __init__(self,
                 path_to_dxf:str,
                 acc=0.1,
                 vis_scale=10.0,
                 text=True,
                 format="A4"):

        self.name = path_to_dxf.split("/")[-1].split(".")[0]
        print("name: " + self.name)

        self.acc = acc

        self.file = FCODE(size=format, name=self.name)
        self.reader = Reader(name=path_to_dxf, acc=self.acc)

        self.instructions = self.reader.read()

        self.vis = Visual("A4", scale=vis_scale)

    def generate_instructions(self):
        for segments in self.instructions: #segments are colsed loops of lines 

            x, y = segments[0][0], segments[0][1]
            
            # move to next segment with lifting the nozzle
            if not (x, y) == (self.vis.nozzle_x, self.vis.nozzle_y): 
                self.vis.penup()
                self.file.add_instruction(Instruction("PUP"))

                self.vis.move(x, y) # move to first segment pos
                self.file.add_instruction(Instruction("MOV", x, y))

                self.vis.pendown()
                self.file.add_instruction(Instruction("PDN"))

            else: # the nozzle is already at the position -> no need for movement
                pass

            for segment in segments[1:]: # add each coordinate of the loop / segment
                self.file.add_instruction(Instruction("MOV",  *segment))
                self.vis.move(*segment)


    def save(self, show_visualization=True):
        self.file.save()

        if show_visualization:
            self.vis.show()
        