############################################################################
#   Written by Zhuang Li, Purdue University. Last modified at 2021-03-13   #
#           Tested on Python 3.7.0 Pandas v0.22.0  Numpy v1.19.1           #
#           Tested on RELION 3.0 / 3.1, Cryosparc 2.9                      #
############################################################################
import argparse
import os
import pandas as pd
import numpy as np
import sys
from RelionTools import *

class STAR():
    """
        Basic Class to Transform Relion Particle Star File into Pandas DataFrame.
        This class has built-in function to read, write, modify and delete data from the DataFrame
        The functionalities include:
            * Retireve particles information from cs and convert into star file
            * Human recentering of particles based on 2D classification
            * Quick information of common parameters(Under development)
            * Reducing particle of dominant views(Under development)
            * Plot informartion based on star file(Under development)
            * Split micrograph into different optics group (Under development)
            * ....
        Attributes of a star class includes:
            contents
            version
            length
            shape
            col_name
            ....

    """

    def __init__(self, filename, idx = "rlnImageName", wipe_zero = True, inplace = False):

        assert ( ".star" in filename ), "Your input {} has no .star suffix...".format(filename)
        self._get_header(filename)
        self._get_ctf()

        try:
            self._content = pd.read_csv(filename, sep = '\s+', skiprows = self._particle_start_nr,\
                 names = self._particles_columns, skipinitialspace = True, skip_blank_lines = True, index_col = idx) 
        except ValueError:
            print_error("rlnImageName Column not found from star file")
        except FileNotFoundError:
            print_error("Specified File doesn't exist")

    def _get_header(self, filename):

        self._version = "3.0"
        self._optics_header = ""
        self._optics = []
        self._particles_header = ""
        self._particles_columns = []
        flag_30 = False
        flag_31_opt = False
        flag_31_pctl = False
        blnk = re.compile(r"^\s*$")

        with open(filename) as f:
            for nr, ln in enumerate(f.readlines(1000)):
                if ln.startswith("data_"):
                    if "optics" in ln:
                        self._version = "3.1"
                        self._optics_header = "data_optics\nloop_\n"
                        self._particles_header = "data_particles\nloop_\n"
                        flag_31_opt = True
                    elif "particles" in ln:
                        flag_31_pctl = True
                    else:
                        self._version = "3.0"
                        self._particles_header = "data_\nloop_\n"
                        flag_30 = True
                    continue

                elif ln.startswith("loop_") or ln.startswith("#") or re.match(blnk, ln):
                    continue

                else:
                    if flag_31_pctl or flag_30:
                        if ln.startswith("_rln"):
                            self._particles_columns.append(ln.split(" ")[0][1:])
                            self._particle_start_nr = nr + 1
                    else:
                        self._optics.append(ln)

        print_info("The star file is from RELION {}".format("3.0 or older" if self._version == "3.0" else "3.1 or newer"))
    
    def _get_ctf(self):
        if self._version == "3.1":
            cols, vals = [], []
            self._ctf = {}
            for ele in self._optics:
                if ele.startswith("_rln"):
                    cols.append(ele.split(" ")[0][1:])
                else:
                    vals = re.split(r"\s+", ele)
            for i,j in enumerate(cols):
                self._ctf[j] = vals[i]
            print_dict(self._ctf)
            self._mics_apix = float(self._ctf["rlnMicrographOriginalPixelSize"])
            self._image_apix = float(self._ctf["rlnImagePixelSize"])
            self._downscale_factor = self._image_apix // self._mics_apix
            self._image_size = int(self._ctf["rlnImageSize"])
            self._image_dim = int(self._ctf["rlnImageDimensionality"])
            self._voltage = float(self._ctf["rlnVoltage"])
            self._cs = float(self._ctf["rlnSphericalAberration"])
            self._amp = float(self._ctf["rlnAmplitudeContrast"])
        else:
            pass
    #Query basic information of this DataFrame
    def has_required_columns(self, columns):
        return set(columns).issubset(self._content.columns)
    def has_unique_particles_path(self):
        pass
    def get_star_version(self):
        return self._version
    def get_index(self):
        return self._content.index.tolist()
    def get_header_content(self):
        """return the first line until the column name line"""
        return self._particles_columns
    def get_column_content(self, col_name, uniq = True):
        if uniq:
            return list(set(self._content[col_name].tolist()))
        else:
            return self._content[col_name].tolist()
    def get_particle_names(self):
        return self._content.index.tolist()
    def get_particles_path(self):
        return os.path.split(self.get_particle_names()[0].split("@")[1])[0]
    def get_particle_nr(self):
        return self._content.shape[0]
    def get_defocus_range(self):
        return self._content['rlnDefocusU'].min, self._content['rlnDefocusU'].max, self._content['rlnDefocusU'].median
    def get_micrograph_number(self):
        return len(set(self._content['rlnMicrographName']))
    def get_image_apix(self):
        if self._version == "3.0":
            return self._content.iloc[1,'rlnPixelSize'] / self._content.iloc[1,'rlnMaginification']
        else:
            return self._image_apix

    #Filter data from the STAR DataFrame.
    #The following function made change to the dataframe, so 'inplace' option is supported.
    def update_content(self,df):
        self._content = df

    def keep_rows(self, idx_list, inplace = False):
        if set(idx_list).issubset(self._content.index):
            print_info("Original dataset contains all the items in subset")
        else:
            print_error("Original dataset doesn't cover all the items in subset")
        if inplace:
            self._content = self._content.loc[idx_list]
            return self
        else:
            return self._content.loc[idx_list]

    def drop_rows(self, col_name, exclude_list, inplace = False):
        if inplace:
            mask = self._content[col_name].isin(exclude_list)
            df = self._content[~mask]
            return df
        else:
            mask = self._content[col_name].isin(exclude_list)
            df = self._content[~mask]
            return df

    def filter_exclude_rows(self, filters = "", threshold = 0, inplace = False ):
        pass

    def filter_include_rows(self, filters = "", threshold = 0, inplace = False ):
        pass

    def keep_columns(self, column_list, inplace = False):
        if inplace:
            self._content = self._content[column_list]
            return self
        else:
            return self._content[column_list]

    def drop_columns(self, column_list, inplace = False):
        l = list(set(self._col_name).intersection(column_list))
        if inplace:
            self._content.drop(columns = l, axis = 1, inplace = True)
            return self
        else:
            return self._content.drop(columns = column_list, axis = 1, inplace = False)

    #Add additional information columns into the STAR DataFrame, for example OpticsGroups
    def append_columns(self, df, on = "rlnImageName", inplace = False):
        if inplace:
            try:
                self._content.merge(df, on = on)
            except KeyError:
                print_error("Merge criteria isn't present in both DataFrames")
            else:
                return self
        else:
            try:
                new = pd.merge(self._content.reset_index(), df, on = on )
                new.set_index("rlnImageName",inplace = True)
            except KeyError:
                print_error("Merge criteria isn't present in both DataFrames")
            else:
                return new

    #Speficialized function for STAR Modification
    def human_recenter(self, minx, miny, maxx, maxy, d, inplace = True):
        df = self._content[self._content.rlnClassNumber.isin(d.keys())]
        if self.get_star_version() == "3.0":
            downscale_factor = int(input("Please provide the downscale factor of parcticle stacks:\n"))
            for idx, row in df.iterrows():
                cls_number = str(row['rlnClassNumber'])
                offsets = get_offset_xy(row['rlnAnglePsi'], d[cls_number][0] * downscale_factor, d[cls_number][1] * downscale_factor)
                row['rlnCoordinateX'] -= row["rlnOriginX"] + offsets[0]
                row['rlnCoordinateX'] = min(maxx, max(minx, row['rlnCoordinateX']))
                df.loc[idx,"rlnCoordinateX"] = row["rlnCoordinateX"]
                row['rlnCoordinateY'] -= row["rlnOriginY"] + offsets[1]
                row['rlnCoordinateY'] = min(maxy, max(miny, row['rlnCoordinateY']))
                df.loc[idx,"rlnCoordinateY"] = row["rlnCoordinateY"]
            df["rlnOriginX"].values[:] = 0
            df["rlnOriginY"].values[:] = 0
        else:
            for idx, row in df.iterrows():
                clsnr = str(row['rlnClassNumber'])
                offsets = get_offset_xy(row['rlnAnglePsi'], d[clsnr][0] * self._downscale_factor, d[clsnr][1] * self._downscale_factor)
                row['rlnCoordinateX'] -= row["rlnOriginXAngst"] / self._image_apix + offsets[0]
                row['rlnCoordinateX'] = min(maxx, max(minx, row['rlnCoordinateX']))
                df.loc[idx,"rlnCoordinateX"] = row["rlnCoordinateX"]
                row['rlnCoordinateY'] -= row["rlnOriginYAngst"] / self._image_apix + offsets[1]
                row['rlnCoordinateY'] = min(maxy, max(miny, row['rlnCoordinateY']))
                df.loc[idx,"rlnCoordinateY"] = row["rlnCoordinateY"]
            df["rlnOriginXAngst"].values[:] = 0
            df["rlnOriginYAngst"].values[:] = 0

        if inplace:
            print_info("Updating")
            self.update_content(df)
        else:
            return df

    def to_star(self, output_file_name):
        """
            This function writes STAR instance into star file
            Relion 3.1 star file = optics_header + optics + particle_header + particles_column + content
            Relion 3.0 star file = particle_header + particles_column + content
        """
        if self._version == "3.0":
            h = self._particles_header + "_rlnImageName #1\n"
            for i,j in enumerate(self._content.columns.tolist()):
                h += "_{} #{}\n".format(j,str(i+2))
        else:
            h = self._optics_header + "".join(self._optics)
            h += "\n" + self._particles_header + "_rlnImageName #1\n"
            for i,j in enumerate(self._content.columns.tolist()):
                h += "_{} #{}\n".format(j,str(i+2))
        with open(output_file_name, 'w') as star:
            star.write(h)
            self._content.to_csv(path_or_buf = star, sep = " ", header = False, float_format = "%6f")
        print_info("Saved to file: {}".format(output_file_name))