from PIL import Image, ImageDraw, ImageFont
from gen import FCODE

def font(size):
    return ImageFont.truetype("arial.ttf", size)

class Visual:
    scale = 10/1

    nozzle_speed = 10

    def __init__(self, size: tuple[int, int]|str):
        self.nozzle_x, self.nozzle_y = 0.0, 0.0
        self.pen_is_down = False

        if type(size) == str: # convert from str type to x_mm, y_mm
            if size in FCODE.paper_sizes.keys():
                size = FCODE.paper_sizes[size]
            else:
                raise KeyError("Paper size: {" + size + "} is invalid")

        self.size_x = round(size[0] * Visual.scale)
        self.size_y = round(size[1] * Visual.scale)

        self.img = Image.new("RGB", (self.size_x, self.size_y), color="white")
        self.draw = ImageDraw.Draw(self.img)

    def flip_y(self, y:float):
        return self.size_y - y


    def dot(self, pos: tuple[int, int]):
        x, y = pos[0] * Visual.scale, pos[1] * Visual.scale

        self.draw.point((x, y), "black")

    def plot_points(self, points: set[tuple[int, int]]):

        for point in points:
            self.dot(point)

    def line(self, start_pos: tuple[float, float], end_pos:tuple[float, float], c=(0,0,0)):
        s_x, s_y = start_pos[0] * Visual.scale, start_pos[1] * Visual.scale
        e_x, e_y = end_pos[0]   * Visual.scale, end_pos[1]   * Visual.scale

        s_y = self.flip_y(s_y)
        e_y = self.flip_y(e_y)

        self.draw.line((s_x, s_y, e_x, e_y), c, 1)

    def move(self, x, y):

        if self.pen_is_down:
            self.line((self.nozzle_x, self.nozzle_y),(x, y))

        self.nozzle_x, self.nozzle_y = x, y # update x,y nozzle pos

    def penup(self):
        self.pen_is_down = False
    def pendown(self):
        self.pen_is_down = True

    def show(self):
        self.img.show("drawing")


