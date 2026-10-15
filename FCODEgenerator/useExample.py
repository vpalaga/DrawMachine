from main import FGenerator

DXF_PATH = r"C:\Users\vit\OneDrive\Documents\GitHub\DrawMachine\FCODEgenerator\dxfexamples\Drawing 1.dxf"


def from_dxf() -> None:
    # create a generating object (optimize=True reorders paths to minimise pen travel)
    gen = FGenerator(DXF_PATH, acc=0.1, vis_scale=10, text=False, optimize=True)

    # generate the FCODE from the provided dxf file
    gen.generate_instructions()

    # writes '<name>.FCODE' to the working directory; pass output_path="..." to change that
    gen.save(show_visualization=True)


def manual() -> None:
    # not a .dxf -> just the name of the future FCODE file, polylines stay empty
    gen = FGenerator("my_square", vis_scale=10)

    gen.travel_to(50, 50)          # pen up + move
    gen.draw_to(100, 50)           # pen down + draw a line
    gen.draw_to(100, 100)
    gen.draw_to(50, 100)
    gen.draw_to(50, 50)

    gen.pen_up()                   # or use the low-level commands directly
    gen.move_to(150, 150)
    gen.pen_down()
    gen.draw_polyline([(150, 150), (180, 150), (165, 175), (150, 150)])
    gen.wait(1)

    gen.pen_up()
    gen.save()                     # writes my_square.FCODE


if __name__ == "__main__":
    # from_dxf()
    manual()