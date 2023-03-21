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
from datetime import datetime, timedelta
import os
from .data_summary import flag_hr


def process_actiheart(hr_files, shift_file, folder_path, participant_num, part_age, trial_start, trial_end):

    # # Heart Rate and Rotation
    # The second file output by the actiheart device contains heartrate and rotation data sampled at a frequency of 1 hz.
    # Read in file
    heart_data = None
    for file in hr_files:
        if heart_data is None:
            heart_data = pd.read_csv(file, sep='\t', skiprows=5, index_col=False)
        else :
            temp = pd.read_csv(file, sep='\t', skiprows=5, index_col=False)
            heart_data = pd.concat([heart_data, temp])
    # Drop unwanted columns
    heart_data.drop(columns={'Movement', 'Status'}, inplace=True)
    # Add date to Time column
    # Add hour, minute and seconds to date
    heart_data['Time'] = heart_data["Time"].apply(lambda x: trial_start.replace(hour=int(x[:2]), minute=int(x[3:5]), second=int(x[6:]), microsecond=0))
    heart_data.sort_values(by=["Time"])
    if len(shift_file) > 0:
        file = open(shift_file[0], 'r')
        shift = file.readline()
        file.close()
        shift = timedelta(seconds=int(shift))
        # print(shift)
        heart_data['Time'] = heart_data['Time'].apply(lambda x: x - shift)
    heart_data = heart_data.loc[(heart_data['Time'] >= trial_start) & (heart_data['Time'] <= trial_end), :]
    heart_data = flag_hr(heart_data, "Actiheart", part_age)

    # Write output to a csv
    output_path = os.path.join(folder_path, "Processed Data/")
    if os.path.isdir(output_path) is False:
        os.mkdir(output_path)

    output_file = output_path + '/' + participant_num + '_actiheart.csv'
    heart_data.to_csv(output_file, index=False)

    return ["Actiheart", heart_data]





