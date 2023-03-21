import pandas as pd
import numpy as np
import os
from datetime import datetime
from .data_summary import calc_enmo, flag_hr


def reading_check(device_np, device_iter, device_rows, out_row, accel_np, a_iter):
    #   Boundary Checking          Check if current device reading occurs between 2 consecutive acceleration readings
    if device_iter < device_rows and (accel_np[a_iter, 0] <= device_np[device_iter, 0] < accel_np[a_iter + 1, 0]
                                      or accel_np[a_iter, 0] > device_np[device_iter, 0]):
        # Check which actiheart reading is closer to the device reading:
        if abs(accel_np[a_iter, 0] - device_np[device_iter, 0]) <= abs(accel_np[a_iter + 1, 0] - device_np[device_iter, 0]):
            out_row.append(device_np[device_iter, 1])
            device_iter += 1
        else:
            out_row.append(np.nan)

    else:  # No device reading occurred
        out_row.append(np.nan)

    return device_iter, out_row


def timestamp_fitbit(accel_file, hr_file, out_path, participant_id):
    # Read in accel data while dropping first column, 
    accel_list = []
    for file in accel_file:
        accel_list.append(pd.read_csv(file, header=None, names=['Counter', 'Time', 'X', 'Y', 'Z'], usecols=[1,2,3,4], parse_dates=[0], date_parser=lambda x: datetime.fromtimestamp(int(x)/1000)))
    if len(accel_list) > 1:
        accel_data = pd.concat(accel_list, ignore_index=True)
    else :
        accel_data = accel_list[0]
    
    # Save the accel data
    accel_data.to_csv(out_path + participant_id + "_accel.csv", index=False)

    # Read in Heart Rate File
    hr_list = []
    for file in hr_file:
        hr_list.append(pd.read_csv(file, header=None, names=['Counter', 'Time', 'Heart Rate'], usecols=[1,2], parse_dates=[0], date_parser=lambda x: datetime.fromtimestamp(int(x)/1000)))
    if len(hr_list) > 1 :
        hr_data = pd.concat(hr_list, ignore_index=True)
    else:
        hr_data = hr_list[0]
    # Save the HR data
    hr_data.to_csv(out_path + participant_id + '_heart.csv', index=False)
    return accel_data, hr_data

def combine_fitbit(accel_data, hr_data, out_path, participant_id, participant_age, start, end, protocol="PA"):
    # Get the shape of the accel_data
    a_rows, a_cols = accel_data.shape
    # Convert the pandas dataframe to a numpy array
    accel_np = accel_data.to_numpy()
    # Bet shape of heart rate data
    hr_rows, hr_cols = hr_data.shape
    # Convert pandas dataframe to numpy array
    hr_np = hr_data.to_numpy()

    # Initialize the output array
    out_np = np.empty([a_rows + hr_rows, a_cols + hr_cols - 1], dtype="object")

    # initialize iterators (one for acceleration, heart rate, and output)
    a_iter = 0
    h_iter = 0
    o_iter = 0

    while a_iter < a_rows:
        # Initialize a list to hold contents to be added to out_np
        o_row = []
        # Add all accelerometer values
        for value in accel_np[a_iter,:]:
            o_row.append(value)

        # add hr reading if needed
        if a_iter < a_rows - 1:
            h_iter, o_row = reading_check(hr_np, h_iter, hr_rows, o_row, accel_np, a_iter)
        else :
            o_row.append(np.nan)

        # Add o_row to the output
        out_np[o_iter, :] = o_row

        # Increment iterators
        o_iter += 1
        a_iter += 1

    #  If Accel ends early add remaining HR readings
    while h_iter < hr_rows:
        o_row = []

        o_row.append(hr_np[h_iter, 0])

        for i in range(a_cols - 1) :
            o_row.append(np.nan)

        o_row.append(hr_np[h_iter, 1])

        out_np[o_iter, :] = o_row
        h_iter += 1
        o_iter += 1


    # Convert numpy array to pandas dataframe:
    final_df = pd.DataFrame(out_np, columns=["Time", "X", "Y", "Z", "Heart Rate"])
    final_df.drop(final_df.iloc[o_iter:].index, inplace=True)
    # Convert from meteres per second squared to Gs
    final_df[["X", "Y", "Z"]] = final_df[["X", "Y", "Z"]].applymap(lambda x: x/9.8)
    # Get Second Fraction
    sec_frac = final_df["Time"].apply(lambda x: x.microsecond)
    # Insert Second Fraction into df
    final_df.insert(1, "Second Fraction", sec_frac)

    # Flag Heart Rate
    flagged_hr = flag_hr(final_df, "Fitbit", participant_age, protocol=protocol)

    final_df = final_df.merge(flagged_hr, how='left', left_on=final_df.index, right_on=flagged_hr.index)
    final_df.drop(columns=["key_0", "Time_y", "Heart Rate_y"], inplace=True)
    final_df.rename(columns={"Time_x": "Time", "Heart Rate_x": "Heart Rate"}, inplace=True)

    # Create a Processed Data folder and then write the data as a csv to it
    output_path = os.path.join(out_path, "Processed Data")
    if os.path.isdir(output_path) is False:
        os.mkdir(output_path)

    final_df = final_df.loc[(final_df['Time'] >= start) & (final_df['Time'] <= end), :]

    final_df[['X', 'Y', 'Z']] = final_df[['X', 'Y', 'Z']].apply(pd.to_numeric)
    mag, enmo = calc_enmo(final_df.loc[:, ["X", "Y", "Z"]])
    final_df.insert(5, "Magnitude", mag)
    final_df.insert(6, "ENMO", enmo)

    output_file = output_path + '/' + participant_id + '_fitbit.csv'
    final_df.to_csv(output_file, index=False)

    return ["Fitbit", final_df]
