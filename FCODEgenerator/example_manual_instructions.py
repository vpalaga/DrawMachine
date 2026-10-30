import math

from ezdxf.math import Vec2

from main import FGenerator
import random
from gen import PAPER_SIZES

bounds_x, bounds_y = PAPER_SIZES["A4"]

offset = 8

gen = FGenerator("rnd_path", acc=0.1, vis_scale=10, text=False, optimize=True)

def vec_in_bounds(v:Vec2)->bool:
    if not ( offset <= v.x <= bounds_x-offset):
        return False
    if not ( offset <= v.y <= bounds_y-offset):
        return False
    return True



def rnd_vec(from_v: Vec2)->Vec2:
    r = random.triangular(30,20, 1)
    a = random.randint(0,359)

    dx = round(math.cos(a)*r)
    dy = round(math.sin(a)*r)

    return Vec2(dx, dy) + from_v

def rnd_vec_in_bounds(from_v:Vec2)->Vec2:
    v = rnd_vec(from_v)
    while not vec_in_bounds(v):
        v = rnd_vec(from_v)

    return v

start = Vec2(bounds_x // 2, bounds_y // 2)

gen.travel_to(*start)

for n in range(20):
    start = rnd_vec_in_bounds(start)
    gen.draw_to(*start)

gen.save()
