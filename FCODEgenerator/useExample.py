from main import FGenerator

DXF_PATH = r"C:\Users\vit\OneDrive\Documents\GitHub\DrawMachine\FCODEgenerator\dxfexamples\Drawing 2A4.dxf"

if __name__ == "__main__":
    # create a generating object (optimize=True reorders paths to minimize pen travel)
    gen = FGenerator(DXF_PATH, acc=0.1, vis_scale=10, text=True, optimize=True)

    # generate the FCODE from the provided dxf file
    gen.generate_instructions()

    # writes '<name>.FCODE' to the working directory; pass output_path="..." to change that
    gen.save(show_visualization=True)