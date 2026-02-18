from PIL import Image, ImageDraw
import random

sqares = 800
size = sqares//2

pixels_p_sqare = 1
BLACK = (0,0,0)
WHITE = (255,255,255)

w_h= sqares*pixels_p_sqare

img = Image.new("RGB", (w_h, w_h),color=WHITE)
drw = ImageDraw.Draw(img)

def grd():
    for y in range(sqares):
        drw.line([(0, y*pixels_p_sqare),(w_h, y*pixels_p_sqare)], fill=(40,40,40),width=1)
    for x in range(sqares):
        drw.line([(x*pixels_p_sqare, 0),(x*pixels_p_sqare, w_h)], fill=(40,40,40),width=1)

#grd()

def line(x1, y1, x2, y2):
    drw.line([(x1,y1),(x2,y2)],fill=BLACK,width=1)

    
class Stepper:
    def __init__(self):
        self.x = w_h / 2
        self.y = w_h / 2

    def step(self, dir:bool,step:int, type:str): 
        if type == "x":
            if dir:
                new_x = self.x + pixels_p_sqare * step
            else:
                new_x = self.x - pixels_p_sqare * step

            line(self.x, self.y, new_x, self.y)
            self.x = new_x

        elif type == "y":
                
            if dir:
                new_y = self.y - pixels_p_sqare * step
            else:
                new_y = self.y + pixels_p_sqare * step

            line(self.x, self.y, self.x, new_y)
            self.y = new_y
        
        # make nice edges
        #drw.circle((self.x, self.y), 4, BLACK)
    
    def reset(self):
        self.x = w_h / 2
        self.y = w_h / 2

            

class Driver:
    def __init__(self):
        self.xyStepper = Stepper()

    def bresenham(self, stepper: Stepper,lead:int, follow:int, leadDir:bool, followDir:bool, stepper_lead:str):
        bresenhamStep = follow/lead; # needs to be <0, bc follow < lead

        followPos = 0

        for cycle in range(1,lead + 1): # cycle needs to start at 1
            
            followCycle = round(cycle*bresenhamStep)
            
            # check how many are needed for this cycle
            diffFollowCycle = followCycle - followPos
            print(diffFollowCycle)
            # update the followPos to current follow position
            followPos += diffFollowCycle

            #move the steppers accordingly
            if stepper_lead == "x":
                stepper.step(leadDir,1,"x")
                stepper.step(followDir,diffFollowCycle,"y")
        
            else:
       
                stepper.step(leadDir,1,"y")
                stepper.step(followDir,diffFollowCycle,"x")

    def move(self, x:int, y:int)->None:
        x_dir = True if x>0 else False
        print(x_dir)
        y_dir = True if y>0 else False

        x = abs(x)
        y = abs(y)

        if x>y: #x = leads
            self.bresenham(self.xyStepper,x, y,x_dir,y_dir, "x")
        else:
            self.bresenham(self.xyStepper, y, x, y_dir, x_dir,"y") 


def abs_line(x, y):
    drw.line([(w_h/2, w_h/2),
              (x*pixels_p_sqare + w_h/2,-y*pixels_p_sqare + w_h/2)],fill=(255,0,0),width=3)


drv = Driver()
for _ in range(10):

    mv_to = (random.randint(-size,size),random.randint(-size,size))

    #mv_to = (9,7)
    #abs_line(*mv_to)
    drv.move(*mv_to)

    drv.xyStepper.reset()

img.show()
    