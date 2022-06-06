#!/usr/bin/env python
# coding: utf-8

# # Actiheart Processing
# The purpose of this script is to read in output files from an actiheart device and then reformat the data into a more readable format that can be used by another script to align the data with other device data. This script is looking to process 2 files.
# <br><br>
# The first file contains output from 2 different sensors stacked ontop of each other. (ECG and Acceleration) Here is a list of tasks that need to be done to format this file correctly:
# 1. Split the file into two separate csv files one containing ECG and the other containing Accelerometer data
# 2. Read in both files
# 3. Create timestamps for each sensor reading
# 4. Store each file

# In[1]:


import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog
from datetime import datetime, time, timedelta


# In[2]:




def data_split(data, out_path, participant_number) :
    # Need to read through data
    ecg_accel = open(data[0], 'r')
    # This variable is used to determine which section I'm currently iterating through
    section = 1
    # This variable represents the start time of the trial
    start_time = None
    # Create two output files, ecg and acceleration
    ecg = open(out_path + "/" + participant_number + "_ecg_split.csv", "w")
    accel = open(out_path + "/" + participant_number + "_accel_split.csv", "w")
    # Variables created to signify if file is open
    ecg_open = True

    for line in ecg_accel:
        # print(f"{section} : {line}")
        if section == 1: # Checks if iterating through section 1
            if line[:7].lower() == 'started' :
                start_time = datetime.strptime(line[8:-1], "%d-%b-%Y %H:%M")
                print(start_time)
        elif section == 2 : # Checks if iterating through section 2
            ecg.write(line)
        elif section == 3 : # Checks if 3 section of file is reached
            # Closes ECG file
            if ecg_open :
                ecg.close()
                ecg_open = False

            accel.write(line)

        # Looks for blank line. If found it indicates that a section has ended
        if line == "\n" :
            section += 1

    # Close files
    if ecg_open :
        ecg.close()
    accel.close()
    ecg_accel.close()
    return start_time

"""
# In[4]:


# Function used to parse dates to datetime
custom_date_parser = lambda x : start_time + timedelta(seconds=float(x))


# In[6]:


# Now read in ECG File and combine the Date, Time, and Second Fraction into 1 column
ecg_data = pd.read_csv(actiheart_path + "/962_ecg_split.csv", parse_dates = ['Total Seconds'], 
                       date_parser = custom_date_parser)
ecg_data.drop(columns=["Date", "Time"], inplace=True)
ecg_data.rename(columns={"Total Seconds": "ECG Time"}, inplace=True)
sec_frac = ecg_data.pop('Second Fraction')
ecg_data.insert(1, 'Second Fraction', sec_frac)
ecg_data


# In[7]:


# Read in the Accel File and combine The Date, Time, and Second Fraction Column to one column called DateTime
accel_data = pd.read_csv(actiheart_path + "/962_accel_split.csv", parse_dates=['Total Seconds'], 
                         date_parser= custom_date_parser)
accel_data.drop(columns=['Date', 'Time', 'Second Fraction'], inplace=True)
accel_data.rename(columns={"Total Seconds": "Accel Time"}, inplace = True)
accel_data


# # Heart Rate and Rotation
# The second file output by the actiheart device contains heartrate and rotation data sampled at a frequency of 1 hz.

# In[9]:


# Read in file
heart_data = pd.read_csv(actiheart_path + "/962_persec.txt", sep='\t', skiprows=5, index_col=False)
# Drop unwanted columns
heart_data.drop(columns={'Movement', 'Status'}, inplace=True)
# Add date to Time column
date = accel_data.iloc[0,0].to_pydatetime() # Get date from acceleration
# Add hour, minute and seconds to date
heart_data['Time'] = heart_data["Time"].apply(lambda x: date.replace(hour=int(x[:2]), 
                                                                     minute=int(x[3:5]), second=int(x[6:]), microsecond=0))
heart_data.sort_values(by=["Time"])
heart_data


# # Align ECG, Acceleration, and Heart Rate
# Iterate through each file and order all of the readings by time in one dataframe. Since ECG is the finest grain data I will align the rest of the data to ECG

# In[10]:


# First convert 3 data frames to numpy arrays. This is needed because iterating through numpy arrays is much faster than 
# iterating through dataframes.
ecg_np = ecg_data.to_numpy()
accel_np = accel_data.to_numpy()
hr_np = heart_data.to_numpy()

# Get shape of each array
ecg_rows, ecg_col = ecg_np.shape
accel_rows, accel_col = accel_np.shape
hr_rows, hr_col = hr_np.shape

# Calculate number of columns needed for output array
out_col = ecg_col + accel_col + hr_col


# In[11]:


# Intialize output array
out_np = np.zeros([ecg_rows, out_col], dtype="O")
# Initialize variables to represent the current row of each numpy array
ecg_iter = 0
accel_iter = 0
hr_iter = 0
out_iter = 0
# Next I iterate through the heart rate and accelration data until none of there readings occure before the start of the ecg
while accel_np[accel_iter, 0] > ecg_np[ecg_iter, 0] :
    accel_iter += 1

while hr_np[hr_iter, 0] > ecg_np[ecg_iter, 0] :
    hr_iter += 1


# In[12]:


# Iterate through ecg, acceleration, and heart rate. An ecg reading will be added to out_np each time, and acceleration
# and heart rate are added as they occur.
max_jump = timedelta(seconds=1)
out_row = []
while ecg_iter < ecg_rows - 1:
    out_row = []
    # Add ECG to output
    for value in ecg_np[ecg_iter, :] :
        out_row.append(value)
    
    # Check if Acceleration Occured
    if accel_iter < accel_rows and (ecg_np[ecg_iter, 0] <= accel_np[accel_iter, 0] < ecg_np[ecg_iter + 1, 0]):
        # Add Acceleration values to output
        for value in accel_np[accel_iter, :]:
            out_row.append(value)
        
        # Check if next reading is valid:
        if accel_iter < accel_rows -1 and accel_np[accel_iter+1,0] - accel_np[accel_iter, 0] >= max_jump :
            print(f"Bogus reading at {accel_iter+1}")
            accel_iter += 1
         
        accel_iter += 1
    else: # Reading hasn't occured
        for i in range(accel_col):
            out_row.append(np.nan)

    
    # Check if Heart Rate Occured
    if hr_iter < hr_rows and ecg_np[ecg_iter, 0] <= hr_np[hr_iter, 0] < ecg_np[ecg_iter + 1, 0]:
        # Add Acceleration values to output
        # print(f"Heart Iter: {hr_iter} \nHeart Values{hr_np[hr_iter,:]}")
        for value in hr_np[hr_iter, :]:
            out_row.append(value)
        hr_iter += 1
    else: # Reading hasn't occured
        for i in range(hr_col):
            out_row.append(np.nan)



    out_np[out_iter, :] = out_row
    
    ecg_iter += 1
    out_iter += 1

# Add last row of ecg
out_row = []
# Add Ecg
for value in ecg_np[ecg_iter, :] :
    out_row.append(value)
# Add nan for rest
for i in range(accel_col + hr_col):
    out_row.append(np.nan)
# Add to output
out_np[out_iter, :] = out_row


# In[13]:


# Get column names
new_cols = []
for name in ecg_data.columns :
    new_cols.append(name)
for name in accel_data.columns :
    new_cols.append(name)
for name in heart_data.columns :
    new_cols.append(name)


# In[14]:


# Convert output to dataframe
out_df = pd.DataFrame(out_np, columns=new_cols)
out_df.drop(columns = out_df.columns[3], inplace=True)
out_df.drop(columns = out_df.columns[6], inplace=True)
out_df


# In[15]:


out_df.to_csv(actiheart_path + "/Processed Data/962_actiheart.csv", index=False)


"""


