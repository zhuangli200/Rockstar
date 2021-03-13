############################################################################
#   Written by Zhuang Li, Purdue University. Last modified at 2021-03-13   #
#                   Tested on Relion 3.0 and 3.1                           #
############################################################################

import re
import os
import math
import subprocess
from datetime import date
from MyTools import *

# General Relion Tools
def is_relion_callable():
    if subprocess.getstatusoutput("relion_refine --version")[0]:
        print_error("Relion_refine is not callable, please check your environment variables")
    else:
        return True

def is_relion_folder():
    if os.path.isfile("default_pipeline.star") and os.path.isfile(".gui_projectdir"):
        return True
    else:
        return False

def is_empty_folder():
    if len(os.listdir(".")):
        return False
    else:
        return True

def get_relion_version():
    if is_relion_callable():
        p = subprocess.getstatusoutput("relion_refine --version")[1]
    try:
        version = re.findall(r"RELION version: (\d\.\d)", p)[0]
        assert (version in ["3.0", "3.1"]), "Currently supported relion versions are 3.0 and 3.1"
        return version
    except IndexError:
        print_error("Failed to get the relion version")

def get_image_dimensions(image, dimension = "y"):
    """Get dimension info of movies, micrograph, particles_stack, and class_average_stack"""
    dim = {}
    cmd_output = subprocess.getstatusoutput("relion_image_handler --i " + image + " --stats")
    idx = re.findall(r"\d+@", cmd_output[1])
    if idx:
        dim["n"] = len(idx)
    else:
        dim["n"] = 1
    dim["x"], dim["y"], dim["z"] = re.findall(r"\(x,y,z,n\)= (\d+) x (\d+) x (\d+) x 1", cmd_output[1])[0]

    result = []
    for d in dimension:
        if d not in "xyzn":
            print_error("Wrong dimension identifier was provided")
        result.append(int(dim[d]))
    return result

#Functions for AutoRelion Programs

def create_relion_project(version, with_manpick_gui = True):
    if is_relion_folder():
        print_error("Cannot create projects on an existing one.")
    with open("default_pipeline.star",'w') as fp:
        fp.write("\ndata_pipeline_general\n\n_rlnPipeLineJobCounter                       1\n\n")
    with open(".gui_projectdir",'w') as fp:
        fp.write("")
    if with_manpick_gui:
        if version == "3.0":
            with open(".gui_manualpickrun.job", "w") as fp:
                fp.write(relion_gui_parameters["manpick"])
            print_info("Added .gui_manualpick.job file to current RELION 3.0 folder")
        elif version == "3.1":
            with open(".gui_manualpickjob.star", "w") as fp:
                fp.write(relion_gui_parameters["manpick"])
            print_info("Added .gui_manualpickjob.star file to current RELION 3.1 folder")
        else:
            print_error("Unknown relion version")

def execute_relion_pipeliner(cmd):
    print_info("Scheduling job")
    if not subprocess.getstatusoutput(str(cmd))[0]:
        print_info("Job scheduling succeeded")
    else:
        print_error("Job scheduling failed")

def change_script_permission(bash_file):
    """This function is used to make the bash script executable"""
    print_info("Changing bash file to be executable")
    if not subprocess.getstatusoutput("chmod +x " + bash_file)[0]:
        print_info("Ready to go!")
    else:
        print_error("Cannot change the file permission of {}".format(bash_file))

def relion_cmd_parser(para_list, skip_link = False):
    """This parse only works for relion 3.0 """
    para_dict={}
    para_dict["time"] = "5"
    para_dict["mpi"] = "4"
    if skip_link:
        para_dict["skip_link"] = "#"
    else:
        para_dict["skip_link"] = ""

    for ele in para_list:
        if "relion_star_loopheader" in ele:
            para_dict["add_header_cmd"] = ele
        elif "ls -rt" in ele:
            para_dict["import_cmd"] = ele
        elif "relion_run_motioncorr_mpi" in ele:
            para_dict["mc_cmd"] = ele 
        elif "relion_run_ctffind" in ele:
            para_dict["ctf_cmd"] = ele
        elif "relion_autopick_mpi" in ele:
            para_dict["autopk_cmd"] = ele
        elif "coords_suffix_autopick.star" in ele:
            para_dict["autopk_prefix"] = ele
        elif "relion_preprocess_mpi" in ele:
            para_dict["extract_cmd"] = ele
            para_dict["extract_job"] = re.findall(r"Extract/(job[0-9]{3})",ele)[0]
        else:
            pass
    return para_dict

def logic_check(para_dict):
    """This checks if the commands collected from relion gui are complete and logically right"""
    try:
        para_dict["import_cmd"]
        para_dict["ctf_cmd"]
        para_dict["autopk_cmd"]
        para_dict["extract_cmd"]
    except KeyError as err:
        print_error("No {} command is found from relion output".format(err.args[0]))
    return True

def get_pipeline_input(filename = "default_pipeline.star"):
    """ This function works for 3.0 and 3.1"""
    content = []
    flag = False
    with open(filename, "r") as fp:
        for ln in fp.readlines():
            if "data_pipeline_input_edges" in ln:
                flag = True
            if "data_pipeline_output_edges" in ln:
                flag = False
            if flag:
                content.append(ln.lstrip(" ").rstrip(" "))
    content.reverse()
    return content

def get_parent_job(nr, content):
    """ This function works for 3.0 and 3.1"""
    try:
        p = {}
        c = "".join(content)
        p["extract_cmd"] = "Extract/job{:03}".format(nr)
        p["autopk_cmd"] = re.findall("(AutoPick/job\d{3}).*" + p["extract_cmd"], c)[0]
        p["autopk_prefix"] = p["autopk_cmd"]
        p["ctf_cmd"] = re.findall("(CtfFind/job\d{3}).*" + p["autopk_cmd"], c)[0]
        result = re.findall("(MotionCorr/job\d{3}).*" + p["ctf_cmd"],c)
        if result:
            p["mc_cmd"] = result[0]
            p["import_cmd"] = re.findall("(Import/job\d{3}).*" + p["mc_cmd"], c)[0]
        else:
            p["import_cmd"] = re.findall("(Import/job\d{3}).*" + p["ctf_cmd"], c)[0]
    except IndexError:
        print_error("Missing jobs")
    
    print_dict(p)
    return p

def collect_relion_commands(nr, p):
    """ This function is used to read the note.txt and retrieve the command under certain job folders.
        It only works for relion 3.1
    """

    def collect_relion_command(jb, keyword = "relion_"):
        cmd = ""
        filename = os.path.join(jb, "note.txt")
        assert os.path.isfile(filename), filename + " doesn't exist."
        with open(filename) as fp:
            for ln in fp.readlines():
                if keyword in ln:
                    cmd = ln.rstrip("\n").rstrip(" ").lstrip(" ")
        if cmd:
            return cmd
        else:
            print_error("No desirable command is found from the file")

    para_dict = {}
    para_dict["time"] = "5"
    para_dict["mpi"] = "4"
    para_dict["skip_link"] = "#"
    para_dict["extract_job"] = "job{:03}".format(nr)

    for k,v in p.items():
        if k == "autopk_prefix":
            para_dict[k] = collect_relion_command(v, keyword = "echo")
        else:
            para_dict[k] = collect_relion_command(v)
    return para_dict

# Function specific to Human recenter mode of Rockstar.py
def relion_display_parser(mrcs, class_number, scale = '1'):
    """This function records and parses the relion_display output after mouse click on the class average
        It only works for relion 3.0
    """
    d = {}
    for i in range(class_number):
        cls = str(i+1) 
        cmd_stdout = subprocess.getstatusoutput("relion_display --i " + cls + "@" + mrcs + " --scale " + scale)

        if cmd_stdout[0]:
            print_error("Something is wrong with relion_display, exiting....")

        if cmd_stdout[1].startswith(" Image value"):
            # xy = re.findall(r"\(-?[0-9]{1,4},-?[0-9]{1,4}\)",cmd_stdout[1])[-1][1:-1].split(',')
            # Old regex, should be the same with the new one.
            xy = re.findall(r"Image value at \(\d+,\d+\) or \((-?\d+),(-?\d+)\)", cmd_stdout[1])[0]
            d[cls] = (int(xy[0]), int(xy[1]))
            print_info("Center of cls {} is {}, {}".format(cls, d[cls][0], d[cls][1]))

        elif cmd_stdout[1].startswith("distance"):
            d[cls] = (0,0)
            print_info("Class {} is already centered".format(cls))

        else:    
            print_info("Class {} is discarded".format(cls))

    return d

def get_offset_xy(psi, dx, dy):
    """This function records and parses the relion_display output after mouse click on the class average"""
    cos_val = math.cos( float(psi) / 180 * 3.14 )
    sin_val = math.sin( float(psi) / 180 * 3.14 )
    offsetx = dx * cos_val + dy * sin_val
    offsety = dy * cos_val - dx * sin_val
    return (offsetx, offsety)

#
