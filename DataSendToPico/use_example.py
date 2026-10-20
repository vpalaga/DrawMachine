from pathlib import Path

from src.Controller import Controller

fcode_path = Path(__file__).resolve().parents[1] / "FCODEgenerator" / ".fcodes" / "pcb_case.FCODE"
cont = Controller(str(fcode_path))

cont.do_file()