from main import FGenerator

# create a generatin object
gen = FGenerator(r'C:\Users\vit\OneDrive\Documents\GitHub\DrawMachine\FCODEgenerator\simpleShape.dxf', acc=.1, vis_scale=10, text=False)

# generate the FCODE from the provided dxf file
gen.generate_instructions()
 # the save format / location can be configured under gen.py method: save()
gen.save()