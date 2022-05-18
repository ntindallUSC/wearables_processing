#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import datetime
import numpy as np
import time
import glob
import tkinter as tk
from tkinter import filedialog
import os.path
from Sleep_Study.processing_scripts.PSG_Processor import psg_process

# ## Read in the PSG Data
# This subsection of code reads in the sample PSG file. Right now I have the explicit path hard coded in. Later once we have a real version I'll replace it.

# In[2]:


# ---------------------------------------------------------------------------------------------------------------------
# This first section of code prompts the user to select the participant folder. This folder will house all of the raw
# data from the sleep study.

root = tk.Tk()
root.winfo_toplevel().title("Select csv files")
root.withdraw()

# Start of dialogue
print("Please select the folder of the participant you wish to process")
participant_path = filedialog.askdirectory()
print(f"Path to Participant Folder: \n{participant_path}")
# Determine the Participant Number
participant_num = participant_path[-10:]
print(f"Participant Number: \n{participant_num}")
# Test
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# This section of code reads in the psg data and time stamps it.
psg_path = participant_path + "/PSG/"
if os.path.isdir(psg_path):
    psg_data = glob.glob(psg_path + "*ebe.txt")
    print(f"Path to Epoch Data:\n{psg_data}")
    psg_summary = glob.glob(psg_path + "*psg.txt")
    print(f"Path to PSG Summary: \n{psg_summary}")
    # This function reads in the psg data and then time stamps it.
    psg = psg_process(participant_num, psg_path, psg_summary[0], psg_data[0])
    # Converts the Time Column to a datetime data type
    psg["Time"] = pd.to_datetime(psg["Time"])
    psg_np = psg.to_numpy()
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
# # Read in the Actigraph Data
# This subsection of code reads the actigraph data into a pandas CSV.
# This line of code specifies the path to the actigraph data
acti_path = participant_path + "/ActiGraph/csv/"
if os.path.isdir(acti_path):
    # This line of code grabs all the data files out of the specified folder
    acti_data = glob.glob(acti_path + "*acti.csv")
    print(f"Actigraph Data Path: \n{acti_data}")
    actigraph = pd.read_csv(acti_data[0], skiprows=10)
    actigraph_np = actigraph.to_numpy()


# I define this function to convert actigraph time stamps to datetime datatype. I will use this function when I iterate
# through the actigraph data.
def actigraph_time_convert(aTime):
    a = datetime.datetime.strptime(aTime, '%m/%d/%Y %H:%M:%S.%f')
    return a
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# # Read in Apple Watch Data
# This subsection of code reads in the processed Apple Watch Data. The path is hard coded in for now.
apple_path = participant_path + "/Apple Watch/Processed Data/"
if os.path.isdir(apple_path):
    apple_data = glob.glob(apple_path + "*apple_data.csv")
    print(f"Apple Data Path: \n{apple_data}")
    apple = pd.read_csv(apple_data[0])
    apple['Time'] = pd.to_datetime(apple["Time"])
    apple_np = apple.to_numpy()
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Read in Garmin Data
# This subsection of code reads in the processed Garmin Data
garmin_path = participant_path + "/Garmin/Processed Data/"
if os.path.isdir(garmin_path):
    garmin_data = glob.glob(garmin_path + "*garmin_data.csv")
    print(f"Garmin Data Path: \n{garmin_data}")
    garmin = pd.read_csv(garmin_data[0])
    garmin["Time"] = pd.to_datetime(garmin["Time"])
    garmin_np = garmin.to_numpy()
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
# # Alignment
# The first step is to get a similar start time for all of my datasets. I will use the PSG start time as the reference. Any samples recorded before the psg start time will be thrown away. Similarly any samples recorded after the PSG ends will also be thrown away.

start_time = psg.iloc[0,0]
print(f"Start time: {start_time}")

# Create counters to keep track of place in each array 
# Also get the shape of each array to so that their aren't any index out of bound errors later
c_psg = 0
r_psg, col_psg = psg_np.shape


c_act = 0
r_act, col_act = actigraph_np.shape

c_app = 0
r_app, col_app = apple_np.shape

c_gar = 0
r_gar, col_gar = garmin_np.shape

# First I will go each array and get rid of any readings that began before the start of the PSG
while c_act < r_act and actigraph_time_convert(actigraph_np[c_act, 0]) < start_time :
    c_act += 1
# print(f"Actigraph Counter: {c_act}")
while c_app < r_app and apple_np[c_app, 0] < start_time :
    c_app += 1
# print(f"Apple Counter: {c_app}")
while c_gar < r_gar and garmin_np[c_gar, 0] < start_time :
    c_gar += 1
# print(f"Garmin Counter: {c_gar}")
# print("Done")


# Now I will use one loop to loop through all of the data and and as the times coincide I will add the appropriate
# columns to the output.
# I will be outputting all of this alligned data to a numpy array. Here I will intialize the output array
# and the counter of the array.
# output = np.zeros([r_act, 15], dtype=object)
output = np.zeros([r_act, 19], dtype=object)
# Here I initalize a row counter for the ouput array
c_out = 0

# The output data will the same amount of rows as actigraph and 15 columns this is what it will look like:
#    0         1          2              3          4       5        6        7         8          9        10         11        12         12       14
# [Time, ACTIGRAPH_X, ACTIGRAPH_Y, ACTIGRAPH_Z, APPLE_X, APPLE_Y, APPLE_z, APPLE_HR, GARMIN_X, GARMIN_Y, GARMIN_Z, GARMIN_HR, PSG_EPOCH, PSG_BP, PSG_STG]
# ACTIGRAPH will be 0-3
# APPLE will be 4-7
# GARMIN will be 8-11
# PSG will be 12-14
i = 0
# Here I begin to align the data
begin = time.time()
print("BEGIN ALIGNMENT")
while c_act < r_act :
    # Create an empty list that acts as a row in the output array
    # I will add each set of data to the list as needed and then set the row
    # of the output array equal to the list.
    row = []
    
    # Adds the actigraph reading to the row. Because this is the finest grain data this should
    # be added each row.
    for column in actigraph_np[c_act]:
        row.append(column)
    
    
    # Check if the apple reading should also be added to the row. I do this by comparing it's time with the actigraph time.
    # If the apple reading time less than or equal to the actigraph reading time then it should be added. 
    if c_app < r_app and apple_np[c_app, 0] <= actigraph_time_convert(actigraph_np[c_act, 0]) :
        # Use the for loop to append each data entry (besides the time) from apple row
        # for column in apple_np[c_app, 1:]:
        for column in apple_np[c_app, 0:]:
            row.append(column)
        # After adding the row increment the row counter
        c_app += 1
    # If an apple reading doesn't belong on the row, I then fill the row with nan values
    else :
        # I use range of 4 here because I add 4 Apple entries to each row.
        # for empty in range(4):
        for empty in range(5) :
            row.append(np.nan)
        
    # Check if the Garmin reading should be added to the row in the same manner as the apple data.
    # Since the garmin data has 25 readings per second without a clear time stamp, each 25 readings
    # are added to 25 consecutive actigraph readings
    if c_gar < r_gar and garmin_np[c_gar, 0] <= actigraph_time_convert(actigraph_np[c_act, 0]) :
        # Use a for loop to add each data entry (besides the time) from the garmin row
        # for column in garmin_np[c_gar, 2:]:
        for column in garmin_np[c_gar, 0:]:
            row.append(column)
        # After adding the data from the garmin row increment row count
        c_gar += 1
    # This else will add nan values to the row if a garmin reading hasn't occured
    else :
        # 4 is used here again because each row should have 4 garmin readings
        # for i in range(4):
        for i in range(6):
            row.append(np.nan)
    
    # Check if the PSG reading should be added to the row.
    if c_psg < r_psg and psg_np[c_psg,0] <= actigraph_time_convert(actigraph_np[c_act, 0]) :
        # Add all data entries in the psg row except time
        # for column in psg_np[c_psg, 1:]:
        for column in psg_np[c_psg, 0:]:
            row.append(column)
        # Increment the psg row counter
        c_psg += 1
    # This will add nan values if a psg reading hasn't occured
    else :
        # The range is in 3 because thats how many psg values are added to the row
        # for i in range(3):
        for i in range(4):
            row.append(np.nan)

    
    #print(row)
    output[c_out, :] = row
    c_act += 1
    c_out += 1
    if c_psg >= r_psg :
        break
    
print(f"Alignment took {time.time() - begin} seconds to execute")
    
# Output the data to a csv
# headers = ['Time', 'ACTIGRAPH_X', 'ACTIGRAPH_Y', 'ACTIGRAPH_Z', 'APPLE_X', 'APPLE_Y', 'APPLE_Z', 'APPLE_HR', 'GARMIN_X', 'GARMIN_Y', 'GARMIN_Z', 'GARMIN_HR', 'PSG_EPOCH', 'PSG_BP', 'PSG_STG']
headers = ['Time', 'ACTIGRAPH_X', 'ACTIGRAPH_Y', 'ACTIGRAPH_Z', 'Apple_Time', 'APPLE_X', 'APPLE_Y', 'APPLE_Z', 'APPLE_HR','Garmin_Time', 'Reading_Num', 'GARMIN_X', 'GARMIN_Y', 'GARMIN_Z', 'GARMIN_HR', 'PSG_Time', 'PSG_EPOCH', 'PSG_BP', 'PSG_STG']
aligned_df = pd.DataFrame(output, columns=headers)
aligned_df.drop(aligned_df.iloc[c_out:].index, inplace=True)


# aligned_df.to_csv(participant_path +"/" + participant_num + "_aligned_data.csv", index=False)
aligned_df.to_csv(participant_path +"/" + participant_num + "_aligned_data.csv", index=False)


