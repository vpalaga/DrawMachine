from segmentFunctions import Instruction
from dxfReader import Reader
from gen import FCODE
from imageHandler import Visual

file = FCODE("A4", "file")
reader = Reader("Drawing 1.dxf", acc=5)

instructions = reader.read()

vis = Visual("A4")

for segments in instructions:
    x, y = segments[0][0], segments[0][1]

    if not (x, y) == (vis.nozzle_x, vis.nozzle_y): # move to next segment with lifting the nozzle
        vis.penup()
        file.add_instruction(Instruction("PENUP"))

        vis.move(x, y) # move to first segment pos
        file.add_instruction(Instruction("MOVE", x, y))

        vis.pendown()
        file.add_instruction(Instruction("PENDOWN"))

    else:
        pass

    for segment in segments[1:]:
        file.add_instruction(Instruction("MOVE",  *segment))
        vis.move(*segment)



vis.show()
file.save()
