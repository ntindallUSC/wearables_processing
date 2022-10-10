#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
from datetime import datetime, timedelta
import numpy as np


def data_alignment(actigraph_data, apple_data, garmin_data, folder_path, participant_num):
    # # Align Data

    # Convert all 5 data frames to numpy arrays
    graph_np = actigraph_data.to_numpy()
    garmin_np = garmin_data.to_numpy()
    apple_np = apple_data.to_numpy()


    # Get dimensions of each array. These will be needed for boundary checking.
    graph_rows, graph_cols = graph_np.shape
    garmin_rows, garmin_cols = garmin_np.shape
    apple_rows, apple_cols = apple_np.shape

    # define ref as the time of the first actigraph reading.
    ref = actigraph_data.iloc[0, 0]
    # Initialize trial start and end
    t_start = datetime(year=ref.year, month=ref.month, day=ref.day, hour=20)
    t_end = t_start + timedelta(hours=10)

    # initialize device iterators and iterate to start of trial
    # actigraph
    graph_iter = 0
    while graph_np[graph_iter, 0] < t_start:
        graph_iter += 1

    # garmin
    garmin_iter = 0
    while garmin_rows > 0 and garmin_np[garmin_iter, 0] < t_start:
        garmin_iter += 1

    # apple
    apple_iter = 0
    while apple_rows > 0 and apple_np[apple_iter, 0] < t_start:
        apple_iter += 1

    # Initialize out_np (The aligned output array)
    out_rows = graph_rows
    out_cols = graph_cols + garmin_cols + apple_cols  # Sum of all device columns
    out_np = np.zeros([out_rows, out_cols], dtype="O")  # Initialize Array
    out_iter = 0  # Initialize output iterator

    # Function that compares 1 device reading with 2 consecutive actiheart  readings and adds then adds to output row
    # Depending on whether the reading occurred
    def reading_check(device_np, device_iter, device_rows, device_cols):
        # Get out_row, and actiheart info
        out_row
        graph_np
        graph_iter

        # Check if device reading has occurred:
        #   Boundary Checking          Check if current device reading occurs between 2 consecutive actiheart readings
        if device_iter < device_rows and (
                graph_np[graph_iter, 0] <= device_np[device_iter, 0] < graph_np[graph_iter + 1, 0]
                or graph_np[graph_iter, 0] > device_np[device_iter, 0]):

            # Check which actiheart reading is closer to the device reading:
            if abs(graph_np[graph_iter, 0] - device_np[device_iter, 0]) <= abs(
                    graph_np[graph_iter + 1, 0] - device_np[device_iter, 0]):
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
    while graph_iter < graph_rows - 1 and graph_np[graph_iter, 0] < t_end and out_iter < out_rows:
        # Initialize out_row as empty row. Through loop data will be added to row and then row will be added to output array.
        out_row = []

        # Add actiheart data
        for value in graph_np[graph_iter, :]:
            out_row.append(value)

        # check if garmin reading has occurred
        garmin_iter = reading_check(garmin_np, garmin_iter, garmin_rows, garmin_cols)
        # check if apple reading has occurred
        apple_iter = reading_check(apple_np, apple_iter, apple_rows, apple_cols)


        # Add out_row to out_np
        out_np[out_iter, :] = out_row

        # Increase actiheart and output iterators
        graph_iter += 1
        out_iter += 1

    # Get names for columns of out_np
    new_cols = []
    # This adds all of the column names to new_cols
    new_cols.extend(actigraph_data.columns)
    new_cols.extend(garmin_data.columns)
    new_cols.extend(apple_data.columns)

    # This labels the columns by which device the column came from
    for i in range(len(new_cols)):
        if i <= graph_cols - 1:
            new_cols[i] = "Actigraph " + new_cols[i]
        elif i <= graph_cols + garmin_cols - 1:
            new_cols[i] = "Garmin " + new_cols[i]
        else:
            new_cols[i] = "Apple " + new_cols[i]

    out_df = pd.DataFrame(out_np, columns=new_cols)
    out_df = out_df.iloc[:out_iter, :]

    # Output File
    output_file = folder_path + "/" + participant_num + "_wearables.csv"
    out_df.to_csv(output_file, index=False)
    return out_df