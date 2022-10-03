import pandas as pd
import numpy as np
from datetime import timedelta


def reading_check(device_np, device_iter, device_rows, device_cols, ref_np, ref_iter, out_row):
    # Check if device reading has occurred:
    #   Boundary Checking          Check if current device reading occurs between 2 consecutive actiheart readings
    if device_iter < device_rows and (
            ref_np[ref_iter, 0] <= device_np[device_iter, 0] < ref_np[ref_iter + 1, 0]
            or ref_np[ref_iter, 0] > device_np[device_iter, 0]):

        # Check which actiheart reading is closer to the device reading:
        if abs(ref_np[ref_iter, 0] - device_np[device_iter, 0]) <= abs(
                ref_np[ref_iter + 1, 0] - device_np[device_iter, 0]):
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

    return device_iter, out_row


def align_psg(data, psg, participant_num, outpath):
    # Convert Data to numpy arrays for faster iteration
    data_np = data.loc[(data[data.columns[0]] >= psg.iloc[0, 0] - timedelta(seconds=30)) &
                       (data[data.columns[0]] <= psg.iloc[-1, 0] + timedelta(seconds=30)), :].to_numpy()
    psg_np = psg.to_numpy()
    # Get the shape of each numpy array
    d_rows, d_cols = data_np.shape
    p_rows, p_cols = psg_np.shape
    # Initialize variables used to iterate through arrays
    d_iter = 0
    p_iter = 0
    # Initialize Output Data Array
    out_rows = d_rows
    out_cols = p_cols + d_cols
    out_np = np.zeros([out_rows, out_cols], dtype="O")
    out_iter = 0

    # Align Data
    while out_iter < out_rows - 1:
        # Initialize Row
        row = []
        # Add data from data_np to row.
        for value in data_np[d_iter, :]:
            row.append(value)

        # Check if PSG data should be added to this row
        p_iter, row = reading_check(psg_np, p_iter, p_rows, p_cols, data_np, d_iter, row)

        # Add row to output array
        out_np[out_iter, :] = row

        d_iter += 1
        out_iter += 1
    # Add last row of data
    row = []
    for value in data_np[d_iter, :]:
        row.append(value)
    for value in psg_np[-1,:]:
        row.append(np.nan)
    out_np[out_iter, :] = row

    # Create a list of column names for the aligned data
    col_names = []
    col_names.extend(data.columns)
    col_names.extend(psg.columns)

    # Convert Numpy array to Pandas CSV and then save data as csv
    final_df = pd.DataFrame(out_np, columns=col_names)
    final_df.to_csv(outpath + participant_num + "_aligned_data.csv", index=False)

