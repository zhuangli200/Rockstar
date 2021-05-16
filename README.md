**Introduction:**  
This program, called rockstar, is developed to facilitate the cryo-EM data processing with RELION.  This program works in three modes, namely subset, hr, and exclude mode.
This program includes the following files:  
- rockstar.py, the main program
- STAR.py, a module file that defines a STAR class which is based on Pandas DataFrame and allows CRUD.
- RelionTools.py, a collection of functions which are used for parsing relion log files and output.  
- MyTools.py, contanining customized printing tools  

**Prerequisite:**  
To properly run the rockstar.py, one can create an conda environment with the rock.yml configuration file `conda env create -f ./rock.yml`. Change the environment name on the first line of rock.yml fille if you prefer another one. Before you use the program, make sure activate the conda environment by `conda activate your_env_name`.

**Usage:**  
> To use the hr mode  
  
The hr mode is designed to re-define the particle center based on RELION 2D class averages. The _data.star from last iteration of 2D classification, the resulting class average stacks, the size (in pixels) of the images from which particles are extracted, and an output filename need to be provied. Optionally, if the class average stacks are too small for you visualize, you can choose to specify a scale factor to make them bigger.  
  
Example commands:  
`python ./rockstar.py hr --i Class2D/jobxxx/run_it025_data.star --mrcs Class2D/jobxxx/run_it025_classes.mrcs --micsx 5760 --micsy 4092 --o new_coords.star`  
`python ./rockstar.py hr --i Class2D/jobxxx/run_it025_data.star --mrcs Class2D/jobxxx/run_it025_classes.mrcs --micsx 5760 --micsy 4092 --o new_coords.star  --scale 2`  
  
After running, the image of individual class from the class average stack will pop out for you to click on.  
For the classes for which you want re-define the center, left mouse click the center of the sub-region of interest.  If not happy with the click, multiple clicks are allowed and the program will only take the last click.  
For the bad classes which you wanna discard, just close the display window without doing anything. For the good classes of which that you dont want change the center, middle mouse click anywhere in the image.  
After navigating all the classses, a star file with new coordinates will be generated, whch can be **directly fed into RELION** for particle extraction.  
  
  
> To use the subset mode  

The subset mode was designed for the situation that you begin the data processing with RELION, jump to cryosparc for some 2D or 3D classification/selection, and want to jump back to RELION. What is only retrieved from the input Cryosparc file is the the columns that is equivalen to RELION _rlnImageName column, other information such as ctf and alignment info are discarded. To convert all the columns of cs to star, csparc2star.py in pyem is recommended. The user must gurantee the cs file is derived form the input star file, otherwise it fails. The output star file is exactly a subset of the input star file, and can be **directly fed into RELION** for further processing.  
  
Example commands:  
`python ./rockstar.py subset --i Extract/job004/particles.star --subset /abs/path/to/J1112/particles_selected.cs --o J1112.star `  
  
> To use a exclude mode  

The exclude mode was designed to exclude particles/images from the input star file. The files provided as exclude parameters is not necessarily as star file.  
`python ./rockstar.py exclude --i Extract/job004/particles.star --exclude Class2D/job005/run_it025_data.star Class2D/job006/run_it025_data.star --o new.star `  
  
Zhuang Li  
zhuangli200@gmail.com  
Mar 13, 2021  
