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
import glob
from datetime import datetime, timedelta, time
import os
from matplotlib import pyplot as plt
from .data_summary import flag_hr


def process_actiheart(hr_files, shift_file, folder_path, participant_num, part_age, trial_start, trial_end, protocol):

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
    if protocol[:2] == 'FL':
        # Need to determine when a new day occurs if test runs over night
        midnight = heart_data.iat[0,0].replace(hour=0, minute=0, second=0)
        midnight_idx = heart_data.index[heart_data['Time'] == midnight][0]
        heart_data.iloc[midnight_idx:, 0] = heart_data.iloc[midnight_idx:, 0].apply(lambda x: x + timedelta(hours=24))
    if len(shift_file) > 0:
        file = open(shift_file[0], 'r')
        shift = file.readline()
        file.close()
        shift = timedelta(seconds=int(shift))
        # print(shift)
        heart_data['Time'] = heart_data['Time'].apply(lambda x: x - shift)
    heart_data = heart_data.loc[(heart_data['Time'] >= trial_start) & (heart_data['Time'] <= trial_end), :]
    heart_data = heart_data.sort_values("Time")
    flagged_hr = flag_hr(heart_data, "Actiheart", part_age)
    heart_data = heart_data.merge(flagged_hr, how='left', on=["Time", "Heart Rate"])

    # Write output to a csv
    output_path = os.path.join(folder_path, "Processed Data/")
    if os.path.isdir(output_path) is False:
        os.mkdir(output_path)

    output_file = output_path + '/' + participant_num + '_actiheart.csv'
    heart_data.to_csv(output_file, index=False)

    return ["Actiheart", heart_data]

def plot_actiheart_hr(data, out_path):
    fig, ax = plt.subplots(figsize=(25, 15))
    ax.plot(data['Time'], data['Heart Rate'], color='blue')
    fig.savefig(out_path)
    plt.close('all')

def process_actiheart_sleep(sleep_files, trial_start, trial_end,):
    sleep_data = []
    for file in sleep_files:
        sleep_data.append(pd.read_excel(file, skiprows=14, usecols=['Time', 'EstSleep', 'Comments']))
    sleep_data = pd.concat(sleep_data)
    sleep_data.rename(columns={"EstSleep": "Stg"}, inplace=True)
    sleep_data['Time'] = sleep_data["Time"].apply(lambda x: datetime.combine(trial_start.date(), x))
    # Need to determine when a new day occurs if test runs over night
    midnight = sleep_data.iat[0, 0].replace(hour=0, minute=0, second=0)
    midnight_idx = sleep_data.index[sleep_data['Time'] == midnight][0]
    sleep_data.iloc[midnight_idx:, 0] = sleep_data.iloc[midnight_idx:, 0].apply(lambda x: x + timedelta(hours=24))
    sleep_data = sleep_data.loc[(sleep_data['Time'] >= trial_start) & (sleep_data['Time'] <= trial_end), :]
    return ["Actiheart Sleep", sleep_data]

if __name__ == "__main__":
    print("Testing Actiheart processing")
    # Initialize parameters for test
    participant_num = "2502"
    participant_age = 10
    trial_start = datetime(year=2023, month=4, day=10, hour=9, minute=28)
    trial_end = datetime(year=2023, month=4, day=10, hour=16, minute=18)
    protocol= "FL-camp"
    actiheart_path = "C:/Users/Nick/Watch_Extraction/Free_Living/Test_Data/2502/camp/ActiHeart data/"
    actiheart_files = glob.glob(actiheart_path + "*_hr*.txt")
    shift_files = glob.glob(actiheart_path + "*shift.txt")
    # Call functions
    test = process_actiheart(actiheart_files, shift_files, actiheart_path, participant_num, participant_age, trial_start, trial_end, protocol)
    print("Plotting results")
    plot_actiheart_hr(test[1], actiheart_path + "/Processed Data/" + participant_num + "_" + protocol.split("-")[1] + '_hr.png')





