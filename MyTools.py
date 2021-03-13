###########################################################################
#  Written by Zhuang Li, Purdue University. Last modified at 2021-03-13   #
###########################################################################
import sys
def print_info (s, verbose = True):
    if verbose:
        print("\033[1m\033[34mINFO : {}\033[0m".format(s))
    else:
        return

def print_dict(d):
    for k, v in d.items(): 
        print ("\033[1m\033[34mKey:{:>35},   Value: {:>25},  Type:{:>25}\033[0m".format(k, str(v), str(type(v))))

def print_error (s, verbose= True, do_exit = "True"):
    if verbose:
        if do_exit:
            print("\033[1m\033[31mERROR: {}, exiting...\033[0m".format(s))
            sys.exit(-1)
        else:
            print("\033[1m\033[31mERROR: {}.\033[0m".format(s))
    else:
        return

def print_warning (s, verbose = True):
    if verbose:
        print("\033[1m\033[33mWARNING: {}\033[0m".format(s))
    else:
        return

def print_prompt(title, options, numbered = True, with_input = True):
    print("\033[1m" + title + ":\033[0m")
    if numbered:
        for idx, option in enumerate(options):
            print(str(idx) + ": " + option)
    else:
        for option in options:
            print("* " + option)
    print("")
    if with_input:
        return input()
    else:
        return

def get_user_input(hint, options = [], dtype = str):
    def get_ip(hint):
        try:
            return input("\033[1m" + hint + ":\033[0m\n")
        except KeyboardInterrupt:
            print_error("Give Up Doing Something")
    def check_type(ip, dtype):
        try:
            dtype(ip)
            return True
        except ValueError:
            print_error("Wrong Data Type was provided",do_exit= False)
            return False
    def check_options(ip, options):
        if ip in options:
            return True
        else:
            print_error("Invalid option was provided",do_exit= False)
            return False
    
    flag = True
    while flag:
        ip = get_ip(hint)
        if ip:
            if check_type(ip, dtype):
                if options:
                    if check_options(dtype(ip),options):
                        flag = False
                else:
                    flag = False
    return dtype(ip)