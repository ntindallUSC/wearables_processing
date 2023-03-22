#!/usr/bin/env python
# coding: utf-8

# In[19]:


import pandas as pd
import numpy as np
from datetime import datetime


# # Read in data
# There are 5 streams of data that must be read in:
# 1. Actigraph (Acceleration sampled at 100 hz)
# 2. Garmin (Heart rate sampled at 1 hz. Acceleration sampled at 25 hz)
# 3. Apple Watch (Heart rate sampled about every 5 seconds. Acceleration sampled at 50 hz)
# 4. ActiHeart (Acceleration sampled at 50 hz. ECG sampled at 256 Hz)
# 5. K5 (Sampled about every 5 seconds)

# In[2]:
# Function that replaces nan activities with label


def convert_to_numpy(some_data):
    device_name = some_data[0]
    # First convert the dataframe to a numpy array
    some_array = some_data[1].to_numpy()
    # Get dimensions of array
    some_rows, some_cols = some_array.shape
    # Initialize an iterator for array
    some_iter = 0
    return [device_name, some_array, some_rows, some_cols, some_iter]

def add_values(device, out_row, curr_reading, next_reading):
    # Check if device reading has occurred:
    #   Boundary Checking          Check if current device reading occurs between 2 consecutive actiheart readings
    if device[-1] < device[2] and (
            curr_reading <= device[1][device[-1], 0] < next_reading
            or curr_reading > device[1][device[-1], 0]):

        # Check which actiheart reading is closer to the device reading:
        if abs(curr_reading - device[1][device[-1], 0]) <= abs(
                next_reading - device[1][device[-1], 0]):
            for value in device[1][device[-1], :]:
                out_row.append(value)
                # Move to next actigraph reading
            device[-1] += 1
        else:
            for i in range(device[3]):
                out_row.append(np.nan)

    else:  # No device reading occurred
        for i in range(device[3]):
            out_row.append(np.nan)

    return out_row, device[-1]

def add_activity_lables(data, activities, flags):
    # Move activity label to the first column
    if "K5 Activity" in data.columns:
        data.drop(columns='K5 Activity', inplace=True)
    data.insert(0, 'Activity', 'Transition', True)
    ref_time = data.columns[1]
    #print(data[ref_time])
    #print(activities['1'][1])

    # Add Label to all data
    data.loc[(data[ref_time] < activities['1'][1]), "Activity"] = "Before Protocol"
    data.loc[(data[ref_time] >= activities[str(len(activities))][2]), "Activity"] = "After Protocol"

    # Here I iterate through my dictionary, accessing each activity
    for acti in activities:
        # Get the tuple of activity information
        acti = activities[acti]
        # Select each row from data who's timestamp falls during and activity and then change the activity column to that
        # activity name
        #       **************Selecting Rows******************  Grab a column -> Set equal to name
        data.loc[(data[ref_time] >= acti[1]) & (data[ref_time] < acti[2]), 'Activity'] = acti[0]

    data.insert(1, "Flags", np.nan, True)
    if len(flags) != 0:
        # This column will hold the names of flag
        for flag in flags:
            # Get the tuple of flag information
            flag = flags[flag]
            # Select each row from data who's timestamp falls during and flag and then change the flag column to that
            # flag name
            #       **************Selecting Rows******************  Grab a column -> Set equal to name
            data.loc[
                (data[ref_time] >= flag[0]) & (data[ref_time] < flag[1]), 'Flags'] = flag[2]
    return data

def add_column_names(a_device, a_list):
    for column in a_device[1].columns:
        a_list.append(a_device[0] + " " + column)
    return a_list


def align(device_list, folder_path, participant_num, protocol="sleep", activities=None, flags=None):
    # The devices in the list are ordered from fastest sampling rate to slowest. The first devices time series should be 
    # used to insert the rest of the devices
    ref_df = device_list.pop(0)
    ref = convert_to_numpy(ref_df)
    
    # Now convert the rest of the devices to numpy arrays.
    np_list = [] # A list of lists containing numpy arrays and details about each array
    for device in device_list:
        np_list.append(convert_to_numpy(device))
    
    # Initialize output array as the same size as the reference
    out_rows = ref[2]
    out_cols = ref[3]
    for device in np_list:
        out_cols += device[3]
    out_np = np.zeros([out_rows, out_cols], dtype="O")  # Initialize Array
    
    # Iterate through each output array
    for i in range(out_rows - 1):
        # Initialize out_row as empty row. Through loop data will be added to row and then row will be added to output array.
        out_row = []

        # Add ref data data
        for value in ref[1][i, :]:
            out_row.append(value)
            
        # Add data from other devices if necessary 
        for device in np_list :
                out_row, device[-1] = add_values(device, out_row, ref[1][i, 0], ref[1][i+1, 0])

        out_np[i, :] = out_row
    out_np = out_np[:-1, :]
    # Initialize a list that contains the column names for out_np
    col_names = []
    col_names = add_column_names(ref_df, col_names)
    for device in device_list:
        col_names = add_column_names(device, col_names)
    out_df = pd.DataFrame(out_np, columns=col_names)


    if protocol == 'PA':
        # Add activity labels to data
        out_df = add_activity_lables(out_df, activities, flags)
    # Output File
    output_file = folder_path + "/" + participant_num + "_aligned.csv"
    out_df.to_csv(output_file, index=False)
    device_list.insert(0, ref_df)

