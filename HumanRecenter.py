import subprocess
import re
import math
from MyTools import *
def relion_display_parser(mrcs, class_number, scale = '1'):
    d={}
    for i in range(class_number):
        cls = str(i+1) 
        cmd_stdout = subprocess.getstatusoutput("relion_display --i " + cls + "@" + mrcs + " --scale " + scale)

        if cmd_stdout[0]:
            print_error("Something is wrong with relion_display, exiting....")

        if cmd_stdout[1].startswith(" Image value"):
            # xy = re.findall(r"\(-?[0-9]{1,4},-?[0-9]{1,4}\)",cmd_stdout[1])[-1][1:-1].split(',')
            # Old regex, should be the same with the new one.
            # How does it work???
            xy = re.findall(r"Image value at \(\d+,\d+\) or \((-?\d+),(-?\d+)\)", cmd_stdout[1])[0]
            d[cls] = (int(xy[0]), int(xy[1]))
            print_info("Center of cls {} is {}, {}".format(cls, d[cls][0], d[cls][1]))

        elif cmd_stdout[1].startswith("distance"):
            d[cls] = (0,0)
            print_info("Class {} is already centered".format(cls))

        else:    
            print_info("Class {} is discarded".format(cls))

    return d

def get_image_dimension(class_average_stack, dimension = "X"):
    if dimension == "N":
        cmd_output = subprocess.getstatusoutput("relion_image_handler --i " + class_average_stack + " --stats")
        if not cmd_output[0]:
            image_dimension = len(re.findall(r"\d+@", cmd_output[1]))
        else:
            print_error("Something went wrong with relion_image_handler")
    if dimension == "X":
        cmd_output = subprocess.getstatusoutput("relion_image_handler --i 1@" + class_average_stack + " --stats")
        if not cmd_output[0]:
            image_dimension = re.findall(r"= (\d+) x \d+ x 1 x 1", cmd_output[1])[0]
        else:
            print_error("Something went wrong with relion_image_handler")
    return int(image_dimension)

def get_offset_xy(psi, dx, dy):
    cos_val = math.cos( float(psi) / 180 * 3.14 )
    sin_val = math.sin( float(psi) / 180 * 3.14 )
    offsetx = dx * cos_val + dy * sin_val
    offsety = dy * cos_val - dx * sin_val
    return (offsetx, offsety)