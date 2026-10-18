from main import FGenerator
from gen import PAPER_SIZES

bounds_x, bounds_y = PAPER_SIZES["A4"]

gen = FGenerator("outline_A4", acc=0.1, vis_scale=10, text=False, optimize=True, join_tol=0.5)

gen.draw_to(0, bounds_y)
gen.draw_to(bounds_x, bounds_y)
gen.draw_to(bounds_x, 0)
gen.draw_to(0, 0)

gen.home()

gen.save()