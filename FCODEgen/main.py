from dxfReader import Reader
from gen import FCODE
from imageHandler import Visual
from segmentFunctions import Instruction


class FGenerator:
    def __init__(self,
                 path_to_dxf:str,
                 acc=0.1,
                 format="A4"):

        self.name = path_to_dxf.split("/")[-1].split(".")[0]
        print("name: " + self.name)

        self.acc = acc

        self.file = FCODE(size=format, name=self.name)
        self.reader = Reader(name=path_to_dxf, acc=self.acc)

        self.instructions = self.reader.read()

        self.vis = Visual("A4")

    def gen_instructions(self):
        for segments in self.instructions:
            x, y = segments[0][0], segments[0][1]

            if not (x, y) == (self.vis.nozzle_x, self.vis.nozzle_y): # move to next segment with lifting the nozzle
                self.vis.penup()
                self.file.add_instruction(Instruction("PENUP"))

                self.vis.move(x, y) # move to first segment pos
                self.file.add_instruction(Instruction("MOVE", x, y))

                self.vis.pendown()
                self.file.add_instruction(Instruction("PENDOWN"))

            else:
                pass

            for segment in segments[1:]:
                self.file.add_instruction(Instruction("MOVE",  *segment))
                self.vis.move(*segment)


    def save(self):
        self.vis.show()
        self.file.save()
