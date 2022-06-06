#!/usr/bin/env python
# coding: utf-8

# ## Welcome
# To begin running the code click the first box of code and then the run button at the top. You will know the code section is done running when their is a nubmer in the square brackets to the left.
# 
# <br><br> The purpose of this script is to upack the Garmin Acceleration Data. Initially the Garmin Accleration data is has 25 readings in one cell corresponding to 1 timestamp. This script unpacks that cell and instead has 1 acceleration reading per row.

# In[1]:


import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
from datetime import timedelta
import xlrd
import subprocess


# In[3]:


# Intialize GUI interface to select file
root = tk.Tk()
root.winfo_toplevel().title("Select csv files")
root.withdraw()
#
print("Please select fit file")
input_path = filedialog.askdirectory()
input_path


# In[4]:


# Convert fit file to csv
jar_path = "C:\\Users\\Nick\\Watch_Extraction\\Garmin\\FIT_SDK\\java\\FitCSVTool.jar"
fit_path = input_path + "/962.fit"
csv_path = input_path + "/962_raw.csv"
subprocess.call(['java', '-jar', jar_path, '-b', fit_path, csv_path, '--data', 'record'])


# In[5]:


# Read file into a Pandas dataframe
data = pd.read_csv(input_path + "/962_raw_data.csv")
data


# In[6]:


# Convert the Garmin timestamp to the excel number format.
# Date garmin was founded
garmin_date = datetime(year=1989, month=12, day=31)
# Changes depending on Daylight savings
offset = timedelta(hours=4)
# The Garmin timestamp is the number of seconds that have passed since the founding of Garmin.
data['record.timestamp[s]'] = data['record.timestamp[s]'].apply(lambda x: timedelta(seconds=x) + garmin_date - offset)
data


# In[8]:


# Here I create a smaller datafram with only the readings that we're interested in
xyz_df = data.loc[:,['record.timestamp[s]','record.developer.0.SensorAccelerationX_HD[mgn]', 'record.developer.0.SensorAccelerationY_HD[mgn]', 'record.developer.0.SensorAccelerationZ_HD[mgn]', 'record.heart_rate[bpm]']]
# Convert that dataframe to a numpy array for faster iteration
xyz_numpy = xyz_df.to_numpy()
rows, columns = xyz_numpy.shape
# Pre allocate an unpacked array. The reason that it has 50 * the amount of rows than the xyz array is in case
# The garmin device records more than 25 readings in a  second. I assume here that it would not record any more than
# 50 readings.
unpack_xyz = np.zeros((rows*50,columns+1), dtype="O")
unpack_xyz


# In[9]:


# Intialize counter to keep track of my place in the merged array.
counter = 0
# Intialize total to keep track of the total amoiunt of readings in the array
total=0
accel_index = np.arange(1,51)

# Iterate through the Garmin array
for readings in xyz_numpy :    # Check to see if the xyz data is empty
    if pd.isna(readings[1]) :
        unpack_xyz[counter, 0] = readings[0]
        unpack_xyz[counter, 1] = 1
        unpack_xyz[counter, 2:] = readings[1:]
        
        counter += 1
        total += 1
    else : # The xyz is not empty
        # Get the amount of accleration readings in the x, y, and z direction
        num_x = len(readings[1].split('|'))
        num_y = len(readings[2].split('|'))
        num_z = len(readings[3].split('|'))

        # Split each cell into a list of readings and then assign each reading to a row in the 
        # unpacked array
        unpack_xyz[counter: counter + num_x, 2] = readings[1].split('|')
        unpack_xyz[counter: counter + num_y, 3] = readings[2].split('|')
        unpack_xyz[counter: counter + num_z, 4] = readings[3].split('|')
        # Add the time to each row
        unpack_xyz[counter: counter + num_z, 0] = readings[0].strftime("%Y-%m-%d %H:%M:%S")
        # Add assign a number to each accleration reading numbering 1 to the amount of readings detected.
        unpack_xyz[counter: counter + num_z, 1] = accel_index[0: num_z]
        
        # Add the heart rate reading to the first accleration reading.
        unpack_xyz[counter, 5] = readings[4]
        counter += num_x
        total += num_x
    
final_df  = pd.DataFrame(unpack_xyz[0:total], columns = ['Time', 'Reading #', 'X', 'Y', 'Z', 'Heart Rate'])
final_df["Heart Rate"] = final_df["Heart Rate"].replace(['0', 0], np.nan)
final_df


# In[10]:


filepath= filedialog.askdirectory()
final_df.to_csv(filepath + "\\962_garmin.csv", index=False)


# In[ ]:




