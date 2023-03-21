import numpy as np
from datetime import datetime, timedelta
import pandas as pd
import os
from .data_summary import calc_enmo, flag_hr



# ## First you need to load the data into the script
# 
# When you run the code block below a file window should open. First you need to select the Sensorlog file that you wish to process. After that select the Auto Health File you wish to process.
# 
# Note you may need to minimize the Jupyter notebook window to see the file selection screen.

# In[2]:


def process_apple(sensor_log, heart_rate, folder_path, participant_num, part_age, trial_start, trial_end, protocol="PA"):
    # Represents how many sensor log files there are
    accel = None
    # delim is initially set to a comma, however the sensor log files can be delimited by various different characters
    delim = ','
    for file in sensor_log:
        # Peek at the file to see what the files is delimited by
        test = open(file, 'r')
        line = test.readline()
        for char in line:
            if char == "|":
                delim = '|'
                break
            elif char == ';':
                delim = ';'
                break
            elif char == ",":
                break
        test.close()

        # If it's the first file read in create the accel dataframe and read in the csv file
        if accel is None:
            accel = pd.read_csv(file, delimiter=delim)
        # Read in a file and append it to the accel data frame
        else:
            temp = pd.read_csv(file, delimiter=delim)
            accel = pd.concat([accel, temp], ignore_index=True)

    # I define this function to remove the timezone from the data. I need to do this because
    # The heart rate data doesn't have a timezone stamp and you cannot compare
    # timezone sensitive data with timezone naive data.
    def accel_time_convert(aTime):
        a = datetime.fromisoformat(aTime[:-6])
        return a

    # I apply the function above to each element in the time column
    accel['loggingTime(txt)'] = accel['loggingTime(txt)'].map(lambda a: accel_time_convert(a))

    # Here I convert the time columns data type to a timestamp. THis allows me to add, subtract,
    # and compare time.
    accel['loggingTime(txt)'] = pd.to_datetime(accel['loggingTime(txt)'])

    accel.drop(columns="CMSensorRecorderAccelerometerTimestamp_sinceReboot(s)", inplace=True)

    # Read in the heart rate file
    heart = pd.read_csv(heart_rate[0])
    # Here I convert the data type in time column in the heart rate data to a timestamp
    heart['Date/Time'] = pd.to_datetime(heart['Date/Time'])

    # Get the shape of the accel and heart datafame. I will use these later
    a_row, a_column = accel.shape
    h_row, h_column = heart.shape

    # Convert the accel and heart dataframes to numpy arrays.
    # It's faster to iterate through numpy arrays than pandas dataframes.
    accel_np = accel.to_numpy()
    heart_np = heart.to_numpy()

    # Here I initialize the numpy array that will hold both heart rate and acceleration data
    # I make the # of rows in this array equal to the amount of rows the sum of the acceleration data
    # and heart rate data. I do this because if for some reason there isn't any overlap in time between
    # The two data sets the data structure could hold all of the information.
    # Initialize output
    out_np = np.empty((a_row + h_row, 5), dtype="object")
    # Initialize output iterator
    out_iter = 0

    # Initialize Acceleration iterator
    a_iter = 0

    # Initialize Heart Rate iterator
    h_iter = 0
    while h_iter < h_row and heart_np[h_iter, 0] < accel_np[a_iter, 0]:
        h_iter += 1

    def reading_check(device_np, device_iter, device_rows, device_cols):
        # Get out_row, and actiheart info
        out_row
        accel_np
        a_iter

        #   Boundary Checking          Check if current device reading occurs between 2 consecutive acceleration readings
        if device_iter < device_rows and (accel_np[a_iter, 0] <= device_np[device_iter, 0] < accel_np[a_iter + 1, 0]
                                          or accel_np[a_iter, 0] > device_np[device_iter, 0]):
            # Check which actiheart reading is closer to the device reading:
            if abs(accel_np[a_iter, 0] - device_np[device_iter, 0]) <= abs \
                        (accel_np[a_iter + 1, 0] - device_np[device_iter, 0]):
                out_row.append(device_np[device_iter, 1])
                device_iter += 1
            else:
                out_row.append(np.nan)

        else:  # No device reading occured
            out_row.append(np.nan)

        return device_iter

    # Begin alignment
    while a_iter < a_row - 1:
        # Initialize output row
        out_row = []

        # Checks for gaps in accelerometer
        if h_iter < h_row and accel_np[a_iter + 1, 0] - accel_np[a_iter, 0] > timedelta(seconds=1):
            # print(f"Gap found between {accel_np[a_iter, 0]} and {accel_np[a_iter + 1, 0]}")
            # Add acceleration value
            for value in accel_np[a_iter, :]:
                out_row.append(value)
            # Check if heart rate value should be added
            if accel_np[a_iter, 0] > heart_np[h_iter, 0]:
                out_row.append(heart_np[h_iter, 1])
                h_iter += 1
            else:
                out_row.append(np.nan)
            # Add reading to output and iterate
            out_np[out_iter, :] = out_row
            out_iter += 1
            a_iter += 1
            # Add heart rates that fall into the gap
            while h_iter < h_row and accel_np[a_iter, 0] > heart_np[h_iter, 0]:
                out_row = [heart_np[h_iter, 0], np.nan, np.nan, np.nan, heart_np[h_iter, 1]]
                out_np[out_iter, :] = out_row
                h_iter += 1
                out_iter += 1
            out_row = []

        for value in accel_np[a_iter, :]:
            out_row.append(value)

        # Check if heart rate reading is needed
        h_iter = reading_check(heart_np, h_iter, h_row, h_column)

        # Add to output
        # print(out_row)
        out_np[out_iter, :] = out_row[:]

        a_iter += 1
        out_iter += 1

    # Adds last row of data
    out_row = []
    for value in accel_np[a_iter, :]:
        out_row.append(value)
    if h_iter < h_row and heart_np[h_iter, 0] <= accel_np[a_iter, 0]:
        out_row.append(heart_np[h_iter, 1])
    else:
        out_row.append(np.nan)
    out_np[out_iter, :] = out_row

    # Convert the merged numpy array to a Pandas dataframe. I do this to make it easier to output as a csv
    final_df = pd.DataFrame(out_np, columns=['Time', 'X', 'Y', 'Z', 'Heart Rate'])
    final_df.drop(final_df.iloc[out_iter:].index, inplace=True)
    # Get Second Fraction
    sec_frac = final_df["Time"].apply(lambda x: x.microsecond)
    # Insert Second Fraction into df
    final_df.insert(1, "Second Fraction", sec_frac)

    # Flag Heart Rate
    flagged_hr = flag_hr(final_df, "Apple", part_age, protocol)

    final_df = final_df.merge(flagged_hr, how='left', left_on=final_df.index, right_on=flagged_hr.index)
    final_df.drop(columns=["key_0", "Time_y", "Heart Rate_y"], inplace=True)
    final_df.rename(columns={"Time_x": "Time", "Heart Rate_x": "Heart Rate"}, inplace=True)

    # Create a Processed Data folder and then write the data as a csv to it
    output_path = os.path.join(folder_path, "Processed Data")
    if os.path.isdir(output_path) is False:
        os.mkdir(output_path)

    final_df = final_df.loc[(final_df['Time'] >= trial_start) & (final_df['Time'] <= trial_end), :]
    final_df[['X', 'Y', 'Z']] = final_df[['X', 'Y', 'Z']].apply(pd.to_numeric)
    mag, enmo = calc_enmo(final_df.loc[:, ["X", "Y", "Z"]])
    final_df.insert(5, "Magnitude", mag)
    final_df.insert(6, "ENMO", enmo)

    output_file = output_path + '/' + participant_num + '_apple.csv'
    final_df.to_csv(output_file, index=False)

    return ["Apple", final_df]