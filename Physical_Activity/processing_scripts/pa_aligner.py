#!/usr/bin/env python
# coding: utf-8

# In[19]:


import pandas as pd
import numpy as np
from datetime import timedelta


# # Read in data
# There are 5 streams of data that must be read in:
# 1. Actigraph (Acceleration sampled at 100 hz)
# 2. Garmin (Heart rate sampled at 1 hz. Acceleration sampled at 25 hz)
# 3. Apple Watch (Heart rate sampled about every 5 seconds. Acceleration sampled at 50 hz)
# 4. ActiHeart (Acceleration sampled at 50 hz. ECG sampled at 256 Hz)
# 5. K5 (Sampled about every 5 seconds)

# In[2]:
# Function that replaces nan activities with label


def align(actigraph_data, garmin_data, apple_data, fitbit_data, actiheart_data, k5_data, folder_path, participant_num, activities, flags):
    # # Align Data
    # Now that the data has been read in the next step is to align the all of the data. Here are the steps to do this:
    # 1. Convert all the dataframes to numpy arrays for faster iteration
    # 2. Throw away readings sampled before the start of the trial. (The k5 started recording when the trial started.)
    # 3. Align all data. (Done be iterating through the actiheart file and adding the other device readings to the closest row.)

    # Convert all 5 data frames to numpy arrays
    graph_np = actigraph_data.to_numpy()
    garmin_np = garmin_data.to_numpy()
    apple_np = apple_data.to_numpy()
    fitbit_np = fitbit_data.to_numpy()
    heart_np = actiheart_data.to_numpy()
    k5_np = k5_data.to_numpy()

    # Get dimensions of each array. These will be needed for boundary checking.
    graph_rows, graph_cols = graph_np.shape
    garmin_rows, garmin_cols = garmin_np.shape
    apple_rows, apple_cols = apple_np.shape
    fitbit_rows, fitbit_cols = fitbit_np.shape
    heart_rows, heart_cols = heart_np.shape
    k5_rows, k5_cols = k5_np.shape

    # Initialize trial start and end
    t_start = activities['1'][1]
    t_end = activities[str(len(activities))][2]

    # initialize device iterators and iterate to start of trial
    # actigraph
    graph_iter = 0
    while graph_rows > graph_iter and graph_np[graph_iter, 0] < t_start:
        graph_iter += 1

    # garmin
    garmin_iter = 0
    while garmin_rows > garmin_iter and garmin_np[garmin_iter, 0] < t_start:
        garmin_iter += 1

    # apple
    apple_iter = 0
    while apple_rows > apple_iter and apple_np[apple_iter, 0] < t_start:
        apple_iter += 1

    # fitbit
    fitbit_iter = 0
    while fitbit_rows > fitbit_iter and fitbit_np[fitbit_iter, 0] < t_start:
        fitbit_iter += 1

    # actiheart
    heart_iter = 0
    while heart_np[heart_iter, 0] < t_start:
        heart_iter += 1

    # k5
    k5_iter = 0
    while k5_rows > k5_iter and k5_np[k5_iter, 0] < t_start:
        k5_iter += 1

    # Initialize out_np (The aligned output array)
    out_rows = k5_rows * 3 * 256  # K5 has 1 reading about every 3 seconds, actiheart is collecting 256 readings a second.
    out_cols = graph_cols + garmin_cols + apple_cols + fitbit_cols + heart_cols + k5_cols  # Sum of all device columns
    out_np = np.zeros([out_rows, out_cols], dtype="O")  # Initialize Array
    out_iter = 0  # Initialize output iterator

    # Function that compares 1 device reading with 2 consecutive actiheart  readings and adds then adds to output row
    # Depending on whether the reading occurred
    def reading_check(device_np, device_iter, device_rows, device_cols):
        # Get out_row, and actiheart info
        out_row
        heart_np
        heart_iter

        # Check if device reading has occurred:
        #   Boundary Checking          Check if current device reading occurs between 2 consecutive actiheart readings
        if device_iter < device_rows and (
                heart_np[heart_iter, 0] <= device_np[device_iter, 0] < heart_np[heart_iter + 1, 0]
                or heart_np[heart_iter, 0] > device_np[device_iter, 0]):

            # Check which actiheart reading is closer to the device reading:
            if abs(heart_np[heart_iter, 0] - device_np[device_iter, 0]) <= abs(
                    heart_np[heart_iter + 1, 0] - device_np[device_iter, 0]):
                for value in device_np[device_iter, :]:
                    out_row.append(value)
                    # Move to next actigraph reading
                device_iter += 1
            else:
                for i in range(device_cols):
                    out_row.append(np.nan)

        else:  # No device reading occurred
            for i in range(device_cols):
                out_row.append(np.nan)

        return device_iter

    # Begin alignment
    while heart_iter < heart_rows - 1 and heart_np[heart_iter, 0] < t_end and out_iter < out_rows:
        # Initialize out_row as empty row. Through loop data will be added to row and then row will be added to output array.
        out_row = []

        # Add actiheart data
        for value in heart_np[heart_iter, :]:
            out_row.append(value)

        # check if actigraph reading has occurred
        graph_iter = reading_check(graph_np, graph_iter, graph_rows, graph_cols)
        # check if garmin reading has occurred
        garmin_iter = reading_check(garmin_np, garmin_iter, garmin_rows, garmin_cols)
        # check if apple reading has occurred
        apple_iter = reading_check(apple_np, apple_iter, apple_rows, apple_cols)
        # check if fitbit reading has occurred
        fitbit_iter = reading_check(fitbit_np, fitbit_iter, fitbit_rows, fitbit_cols)
        # check if k5 reading has occurred
        k5_iter = reading_check(k5_np, k5_iter, k5_rows, k5_cols)

        # Add out_row to out_np
        out_np[out_iter, :] = out_row

        # Increase actiheart and output iterators
        heart_iter += 1
        out_iter += 1

    # Get names for columns of out_np
    new_cols = []
    # This adds all of the column names to new_cols
    new_cols.extend(actiheart_data.columns)
    new_cols.extend(actigraph_data.columns)
    new_cols.extend(garmin_data.columns)
    new_cols.extend(apple_data.columns)
    new_cols.extend(fitbit_data.columns)
    new_cols.extend(k5_data.columns)
    # This labels the columns by which device the column came from
    for i in range(len(new_cols)):
        if i <= heart_cols - 1:
            new_cols[i] = "Actiheart " + new_cols[i]
        elif i <= heart_cols + graph_cols - 1:
            new_cols[i] = "Actigraph " + new_cols[i]
        elif i <= heart_cols + graph_cols + garmin_cols - 1:
            new_cols[i] = "Garmin " + new_cols[i]
        elif i <= heart_cols + graph_cols + garmin_cols + apple_cols - 1:
            new_cols[i] = "Apple " + new_cols[i]
        elif i <= heart_cols + graph_cols + garmin_cols + apple_cols + fitbit_cols - 1:
            new_cols[i] = "Fitbit " + new_cols[i]
        else:
            new_cols[i] = "K5 " + new_cols[i]

    out_df = pd.DataFrame(out_np, columns=new_cols)
    out_df = out_df.iloc[:out_iter, :]

    # Remove microsecond from timestamps
    def micro_remove(aTime):
        if not pd.isnull(aTime):
            aTime = aTime.replace(microsecond=0)
        return aTime

    # Remove microseconds from all timestamps
    out_df['Actiheart ECG Time'] = out_df['Actiheart ECG Time'].apply(lambda x: micro_remove(x))
    if "Actigraph Time" in out_df.columns :
        out_df['Actigraph Time'] = out_df['Actigraph Time'].apply(lambda x: micro_remove(x))
    if "Apple Time" in out_df.columns:
        out_df['Apple Time'] = out_df['Apple Time'].apply(lambda x: micro_remove(x))
    if "Fitbit Time" in out_df.columns:
        out_df["Fitbit Time"] = out_df["Fitbit Time"].apply(lambda x: micro_remove(x))

    # Move activity label to the first column
    activity = out_df['K5 Activity']
    out_df.drop(columns='K5 Activity', inplace=True)
    out_df.insert(0, 'Activity', 'Transition', True)

    # Add Label to all data
    out_df.loc[(out_df['Actiheart ECG Time'] < activities['1'][1]), "Activity"] = "Before Protocol"
    out_df.loc[(out_df['Actiheart ECG Time'] >= activities[str(len(activities))][2]), "Activity"] = "After Protocol"

    # Here I iterate through my dictionary, accessing each activity
    for acti in activities:
        # Get the tuple of activity information
        acti = activities[acti]
        # Select each row from data who's timestamp falls during and activity and then change the activity column to that
        # activity name
        #       **************Selecting Rows******************  Grab a column -> Set equal to name
        out_df.loc[(out_df['Actiheart ECG Time'] >= acti[1]) & (out_df['Actiheart ECG Time'] < acti[2]), 'Activity'] = acti[0]


    out_df.insert(1, "Flags", np.nan, True)
    if len(flags) != 0:
        # This column will hold the names of flagvites
        for flag in flags:
            # Get the tuple of flagvity information
            flag = flags[flag]
            # Select each row from data who's timestamp falls during and flagvtiy and then change the flagvity column to that
            # flagvity name
            #       **************Selecting Rows******************  Grab a column -> Set equal to name
            out_df.loc[
                (out_df['Actiheart ECG Time'] >= flag[0]) & (out_df['Actiheart ECG Time'] < flag[1]), 'Flags'] = \
            flag[2]

    # Output File
    output_file = folder_path + "/" + participant_num + "_aligned.csv"
    out_df.to_csv(output_file, index=False)
    return out_df
