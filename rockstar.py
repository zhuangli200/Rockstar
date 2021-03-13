#! /usr/bin/python
############################################################################
#   Written by Zhuang Li, Purdue University. Last modified at 2021-03-13   #
#               Tested on Python 3.8.8 Pandas v0.22.0                      #
############################################################################
from STAR import *

def getImageName(filename,filepath = ""):
    try:
        cs = np.load(filename)
        image_list = []
        for row in cs:
            idx = "{:06d}".format(int(row["blob/idx"]) + 1)
            filename = row["blob/path"].decode("utf-8").split("/")[-1]
            image_list.append(idx + "@" + filepath + "/" + filename)
        return image_list
    except KeyError:
        print_error("Something went wrong when extracts rlnImageName from cs file")

def ArgumentParse():
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@',formatter_class=argparse.RawDescriptionHelpFormatter,\
                                     description='\033[31mBasic Python Parser for star files\033[0m')
    parser.add_argument("mode", choices = ["subset", "hr", "exclude" ],\
        type = str, help = "Specify which mode you would like to run")
    parser.add_argument("--i", required = True, metavar = '*.star', type = str, \
        help = "Provide the filename of input star")
    parser.add_argument("--o", required = True, metavar = '*.star', type = str, \
        help = "Provide the filename of ouput star")
    parser.add_argument("--subset", required = False, metavar = '*.cs', type = str, \
        help = "Provide the filename of subset star/cs file")
    parser.add_argument("--beamshift", required = False, metavar = '*.csv', type = str, \
        help = "Provide the csv file contining beam shift information")
    parser.add_argument("--mrcs", required = False, metavar = '*.mrcs',type = str, \
        help = "Provide the 2D average file")
    parser.add_argument("--micsx", required = False, metavar = 'X',type = int, \
        help = "Provide the dimensionX of micrographs in pixel, the dimension of k3 images is 5760 x 4092")
    parser.add_argument("--micsy", required = False, metavar = 'Y',type = int, \
        help = "Provide the dimensionY of micrographs in pixel, the dimension of k2 images is 3838 x 3710")
    parser.add_argument("--scale", required = False, default = '1', metavar='1/2/4', \
        type = str, help = "Provide the scale factor for 2D averages display")
    parser.add_argument("--exclude", action = 'append',metavar = "*.star", nargs = "+", \
        help = "Provide star files to exclude")
    parser.add_argument("--retain_subset_columns", action = 'append', metavar = "rlnOriginX rlnOriginY",\
         nargs = "+", help = "When using subset mode to update subset star file, everything except ImageName\
              is discarded. By specifying this parameters with  column names, \
                  the responding information from subset will be retained.")

    args = parser.parse_args()
    if args.o:
        if os.path.exists(args.o):
            print_error("You provided a filename which was taken by another file")
    if args.mode == 'subset':
        if not args.subset:
            print_error("Subset parameter needs to be specified...")
    elif args.mode == 'hr':
        if args.mrcs and args.micsx and args.micsy:
            print_info("Required parameters are present...")
        else:
           print_error("Some of the parameters are missing: --mrcs --micsx --micsy")
    elif args.mode == 'exclude':
        if not args.exclude:
            print_error("Exclude parameters need to be specified...")
    else:
        print_error("Unknown Error")
    return args

#Main

if __name__ == '__main__':

    args = ArgumentParse()

    #Subset mode is used for recovering information from an intact star file
    if args.mode == 'subset':

        all_star = STAR(args.i)

        if args.subset.endswith(".star"):
            sub_star = STAR(args.subset)
            index_list = sub_star.get_index()

        elif args.subset.endswith(".cs"):
            print_info("Cryosparc (cs) file was provided, only rlnImageName column is retrieved...")
            star_file_path = all_star.get_particles_path()
            index_list = getImageName(args.subset, filepath = star_file_path)

        else:
            print_info("Unsupported file type, exiting...")

        if not args.retain_subset_columns:
            new_star = all_star.keep_rows(index_list, inplace = True)
            new_star.to_star(args.o)
        #else:
        #    column_list = args.retain_subset_columns[0]
        #    retained_df = sub_star.keep_columns(column_list)
        #    new_df = all_star.keep_rows(index_list, inplace = True).\
        #        drop_columns(column_list, inplace = True).append_columns(retained_df)
        #df2star(new_df, args.o, all_star_header)
    
    # hr mode is used for running human recentering based on 2D classification job
    elif args.mode == 'hr':
        print_info("Please read instrunction.txt to get to know how to use the program.")
        ip = STAR(args.i)
        if ip.get_star_version() == "3.0":
            assert (ip.has_required_columns(['rlnOriginX','rlnOriginY','rlnClassNumber',\
                'rlnCoordinateX','rlnCoordinateY'])), "Required columns are missing from star file"
        else:
            assert (ip.has_required_columns(['rlnOriginXAngst','rlnOriginYAngst','rlnClassNumber',\
                'rlnCoordinateX','rlnCoordinateY'])), "Required columns are missing from star file"
        mrcs_dim = get_image_dimensions(args.mrcs, dimension = "xn")
        half_box_size = mrcs_dim[0] // 2
        coord_min_x = half_box_size
        coord_min_y = half_box_size
        coord_max_x = args.micsx - half_box_size
        coord_max_y = args.micsy - half_box_size
        class_nr = mrcs_dim[1]
        dict_class_xy = relion_display_parser(args.mrcs, class_nr, scale = args.scale)
        ip.human_recenter(coord_min_x, coord_min_y, coord_max_x, coord_max_y, dict_class_xy)
        ip.to_star(args.o)
        print_info("Done")

    # Info mode is used for presenting basic information of the images in the star file
    elif args.mode == "info":
        input_star_file = SATR(args.i)
        print_info("The toatal number of particles is:"  + input_star_file.get_particle_nr())
        print_info("The total number of micrograph number is " + input_star_file.get_column_content('rlnMicrographName'))
        print_info("The defocus range is" + input_star_file.get_defocus_range())
        print_info("The pixel size of particles is " + input_star_file.get_pixel_size())

    # Exclude mode is used for excluding particles from input star file
    elif args.mode == "exclude":
        micrograph_list = []
        input_star_file = STAR(args.i)
        input_star_header = input_star_file.get_header_content()# Column Name not included
        for f in args.exclude[0]:
            t = STAR(f).get_column_content('rlnMicrographName')
            micrograph_list.extend(t)
        new_df = input_star_file.drop_rows('rlnMicrographName', micrograph_list)    
        df2star(new_df, args.o, input_star_header)

    else:
        print_error("Unknown mode")