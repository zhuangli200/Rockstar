#! /usr/bin/python
########################################################################
# Written by Zhuang Li, Purdue University. Last modified at 2020-03-13 #
# Tested on sklearn, matplotlib, and some others.                      #
# Still under development...                                           #
########################################################################
from sklearn.cluster import KMeans
import rockstar
import matplotlib.pyplot as plt
import pandas as pd
import argparse
import random

def ArgumentParse():
    parser=argparse.ArgumentParser(description = "Clustering micrograph based on beam image shift")
    parser.add_argument("--star", metavar = "*.star", type = str, help = "Provide the filename of MetaData, must contain image_shift_x,image_shift_y,MicrographName columns")
    parser.add_argument("--meta", required = True, metavar = "*.csv", type = str, help = "Provide the star file, MicrographName will be inferred if not contained")
    parser.add_argument("--o", default= "Classify_Result", metavar = '*.*', type = str, help = "Provide the filename of ouput")
    parser.add_argument('--k', default = 0, type = int,help= "How many classes classified into")
    parser.add_argument('--bad', default = "", type = str,help= "Specify file containing bad images")
    #If default is specified, the variable will created anyway...
    parser.add_argument('--save_plot', action = 'store_true',help= "Save plot of classification")
    parser.add_argument('--prepend_optics', action = 'store_true',help= "Prepend old star with Optics Group information")
    return parser.parse_args()

def format_DataFrame(filename):
    """Auto-guess the columns value"""
    df = pd.read_csv(filename)
    assert ( set( df.columns ) == set (["image_shift_x","image_shift_y","MicrographName"])), "Required columns not present in input file"
    x = "image_shift_x"
    y = "image_shift_y"
    df[x] = df[x] * 1000000000
    df[y] = df[y] * 1000000000
    df["OpticsGroups"] = 0
    #for idx in df.index.values:
    #    df.loc[idx, "MicrographName"] = df.loc[idx,"MicrographName"].split(".")[0]
    return df

def remove_file_suffix():
    pass

def classify(df, class_nr):
    unlabeled = df[["image_shift_x", "image_shift_y"]]
    kmeans = KMeans(n_clusters = class_nr) 
    kmeans.fit(unlabeled)
    result = kmeans.fit_predict(unlabeled)
    df["OpticsGroups"] = result
    return df

def plot_unlabeled(df):
    #plt = df.plot.scatter(x = "image_shift_x", y = "image_shift_y",c = "black")
    #filename = ".".join(input_file.split(".")[:-1]) +"_unlabeled.png" 
    plt.scatter(df.image_shift_x, df.image_shift_y, c = "black")
    plt.xlabel("image_shift_x")
    plt.ylabel("image_shift_y")
    plt.show()
    return int(raw_input("\nPlease specify class number:    "))

def get_color_palette(num):
    color_palette = []
    while True:
        color_palette.append((random.randint(0,100) / 100.0, random.randint(0,100) / 100.0, random.randint(0,100) / 100.0))
        if len(set(color_palette)) == num:
            break
    return list(set(color_palette))

def plot_labeled(df, output, cls_nr, save_plot = False):
    color_palette = get_color_palette(cls_nr)
    for idx in df.index.values:
        plt.scatter(df.loc[idx, "image_shift_x"], df.loc[idx, "image_shift_y"], c = color_palette[df.loc[idx, "OpticsGroups"]])
    plt.xlabel("image_shift_x")
    plt.ylabel("image_shift_y")
    if save_plot:
        filename = output + "_labeled.png" 
        plt.savefig(filename)
    plt.show()

def df2csv(df, output, micrograph_name_only = False):
    df.to_csv(path_or_buf = output + ".all", index = False, header = True)
    g = df.groupby("OpticsGroups")
    for cls_nr, mics_subset in g:
        filename = output + ".Group" + str(cls_nr + 1)
        df["MicrographName"].to_csv(path_or_buf = filename, index = False, header = False)

if __name__ == "__main__":

    args = ArgumentParse()

    try:
        meta_df = format_DataFrame(args.meta)
    except IOError:
        print "Failed to read the csv file, exiting"    
        sys.exit(-1)

    if args.bad :
        try:
            with open(args.bad) as fp:
                bad_list = filter(None, fp.read().split("\n"))
        except IOError:
            print "File Permission Problem, no filtration can to be done ..."
        else:
            mask = meta_df["MicrographName"].isin(bad_list)
            meta_df = meta_df[~mask]

    if not args.k:
        class_number = plot_unlabeled(meta_df)
    else:
        class_number = args.k

    meta_df = classify(meta_df, class_number)

    if args.save_plot:
        plot_labeled(meta_df, args.o, class_number, save_plot = args.save_plot)
    else:
        plot_labeled(meta_df, args.o, class_number)

    if args.star:
        star_df = rockstar.STAR(args.star)
        meta_df["OpticsGroups"] = meta_df["OpticsGroups"] + 1
        meta_df.rename(columns={"MicrographName":"rlnMicrographName","OpticsGroups":"rlnOpticsGroup"}, inplace = True)
        new_star = star_df.append_columns(meta_df[['rlnMicrographName','rlnOpticsGroup']], on='rlnMicrographName')
        rockstar.df2star(new_star, args.o + ".star")
    else:
        df2csv(meta_df, args.o)
