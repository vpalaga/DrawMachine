from FCODEgen.main import FGenerator

gen = FGenerator("/home/vit/Downloads/train_v1.dxf", acc=.1, vis_scale=10, text=False)
gen.gen_instructions()
gen.save()