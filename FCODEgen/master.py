from FCODEgen.main import FGenerator

gen = FGenerator("/home/vit/Downloads/train_v1.dxf", acc=0.01)
gen.gen_instructions()
gen.save()