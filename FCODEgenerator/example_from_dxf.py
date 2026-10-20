from main import FGenerator

DXF_PATH = r"dxfexamples\pcb_case.dxf"

def from_dxf() -> None:
    # create a generating object (optimize=True reorders paths to minimize pen travel)
    gen = FGenerator(DXF_PATH, acc=2, vis_scale=10, text=True, optimize=True, join_tol=0.1)

    # generate the FCODE from the provided dxf file
    gen.generate_instructions()

    # writes '<name>.FCODE' to the working directory; pass output_path="..." to change that
    gen.save(show_visualization=True)

if __name__ == "__main__":
    from_dxf()
