#!/usr/bin/env python
# coding: utf-8

# ## Welcome
# To begin running the code click the first box of code and then the run button at the top. You will know the code section is done running when their is a nubmer in the square brackets to the left.
# 
# <br><br> The purpose of this script is to unpack the Garmin Acceleration Data. Initially the Garmin Acceleration data is has 25 readings in one cell corresponding to 1 timestamp. This script unpacks that cell and instead has 1 acceleration reading per row.

# In[2]:
import datetime
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from .agg_data import calc_enmo
from .Data_Plot import flag_hr, hr_helper


# In[3]:


def garmin_process(participant_num, garmin_path, csv_data, age, time):
    print("BEGIN GARMIN PROCESSING")
    # Open summary file to write to.
    summary_path = garmin_path + "\\Processed Data\\" + participant_num + "_garmin_summary.txt"
    summary = open(summary_path, 'w')
    summary.write(f"Participant {participant_num} Summary\n")
    # Read file into a Pandas dataframe
    gaps = []
    num_files = 0
    # Since garmin time stamp is the number of seconds since garmin was founded, this is needed
    # To convert the time stamp to Eastern Standard Time
    garmin_found = datetime(year=1989, month=12, day=31)
    # The US is awesome and follows daylight savings time, so in order to convert to EST we need to ask the user


    for file in csv_data:
        # Checks if the file being read in is the first file
        if num_files == 0:
            data = pd.read_csv(file)
        else:
            # read in next file
            temp = pd.read_csv(file)
            # Find the gap start and end, then convert to time and store in gaps list
            gap_start = timedelta(seconds=int(data.iloc[-1, 0])) + garmin_found
            gap_end = timedelta(seconds=int(temp.iloc[0, 0])) + garmin_found
            gaps.append(f"Gap found between {gap_start} and {gap_end}\n")
            # combine two files
            data = pd.concat([data, temp], ignore_index=True)
        num_files += 1

    # In[4]:
    # Convert the Garmin timestamp to datetime.
    # The Garmin timestamp is the number of seconds that have passed since the founding of Garmin.
    data['record.timestamp[s]'] = data['record.timestamp[s]'].apply(lambda x: timedelta(seconds=x) + garmin_found)

    # if at the time of recording the data, if daylight savings was active.
    if (datetime(year=2022, month=3, day=13) <= data.iloc[0, 0] <= datetime(year=2022, month=11, day=6)) or \
            datetime(year=2023, month=3, day=13) <= data.iloc[0,0] <= datetime(year=2023, month=11, day=5) or \
            datetime(year=2024, month=3, day=10) <= data.iloc[0,0] <= datetime(year=2024, month=11, day=3):
        offset = timedelta(hours=4)
    else:
        offset = timedelta(hours=5)

        # In[5]:
    data['record.timestamp[s]'] = data['record.timestamp[s]'].apply(lambda x: x - offset)
    # Here I create a smaller dataframe with only the readings that we're interested in
    xyz_df = data.loc[:, ['record.timestamp[s]', 'record.developer.0.SensorAccelerationX_HD[mgn]',
                          'record.developer.0.SensorAccelerationY_HD[mgn]',
                          'record.developer.0.SensorAccelerationZ_HD[mgn]', 'record.heart_rate[bpm]']]
    # Convert that dataframe to a numpy array for faster iteration
    xyz_numpy = xyz_df.to_numpy()
    # print(f"Dtype of xyz_numpy: {xyz_numpy.dtype}")
    rows, columns = xyz_numpy.shape
    start = data.iloc[0, 0]
    end = data.iloc[-1, 0]
    # Write start time and end time and number of rows to summary file
    summary.write(f"Start Time: {start} \nEnd Time: {end}\n")
    summary.write(f"The Garmin data initially had {rows} rows of data.\n" +
                  "Each row of data should have 1 heart rate reading and 25 accelerometer readings.\n" +
                  f"In total there would be {rows * 25} rows after unpacking\n")

    # Pre allocate an unpacked array. The reason that it has 50 * the amount of rows than the xyz array is in case
    # The garmin device records more than 25 readings in a  second. I assume here that it would not record any more than
    # 50 readings.
    unpack_xyz = np.zeros((rows * 50, columns + 1), dtype="O")
    # print(f"Dtype of unpack_xyz: {unpack_xyz.dtype}")

    # In[13]:

    # Initialize counter to keep track of my place in the merged array.
    counter = 0
    # Initialize total to keep track of the total amount of readings in the array
    total = 0
    accel_index = np.arange(1, 51)

    # initialize variables to help find 8pm and 6am in the data set.
    # I need these time values so I can write a summary on the data for this time set.
    sleep_start = time[0]
    start_found = False
    start_index = 0
    sleep_end = time[1]
    end_found = False
    end_index = 0

    abnormal_hr = 0
    # Iterate through the Garmin array
    for readings in xyz_numpy:  # Check to see if the xyz data is empty
        # print(xlrd.xldate_as_datetime(readings[0], 0).hour)
        if readings[0] >= sleep_start and start_found is False:
            start_index = counter
            start_found = True
        if start_found is True and readings[0] <= sleep_end and end_found is False:
            end_index = counter
            if readings[0] == sleep_end:
                end_found = True

        if pd.isna(readings[1]) or pd.isna(readings[2]) or pd.isna(readings[3]):
            unpack_xyz[counter, 0] = readings[0]
            unpack_xyz[counter, 1] = 1
            unpack_xyz[counter, 2:5] = np.nan
            unpack_xyz[counter, 5] = readings[4]

            counter += 1
            total += 1
        else:  # The xyz is not empty
            # Get the amount of acceleration readings in the x, y, and z direction
            num_x = len(readings[1].split('|'))
            num_y = len(readings[2].split('|'))
            num_z = len(readings[3].split('|'))

            # Split each cell into a list of readings and then assign each reading to a row in the
            # unpacked array
            unpack_xyz[counter: counter + num_x, 2] = readings[1].split('|')
            unpack_xyz[counter: counter + num_y, 3] = readings[2].split('|')
            unpack_xyz[counter: counter + num_z, 4] = readings[3].split('|')
            # Add the time to each row
            unpack_xyz[counter: counter + num_z, 0] = readings[0]
            # Add the heart rate reading to the first accleration reading.
            unpack_xyz[counter, 5] = readings[4]
            if (readings[4] > 150 or readings[4] < 40) and readings[4] != 0:
                abnormal_hr += 1
            # Add assign a number to each accleration reading numbering 1 to the amount of readings detected.
            unpack_xyz[counter: counter + num_z, 1] = accel_index[0: num_z]

            counter += num_x
            total += num_x

    final_df = pd.DataFrame(unpack_xyz[0:total], columns=['Time', 'Reading #', 'X', 'Y', 'Z', 'Heart Rate'])
    final_df["Heart Rate"] = final_df["Heart Rate"].replace(['0', 0], np.nan)
    # pd.to_numeric(final_df['X'])
    final_df = final_df.astype({"Time": object, "Reading #": int, "X": float, "Y": float, 'Z': float, "Heart Rate": float })
    flagged_hr = flag_hr(final_df, "Garmin", age)
    final_df = final_df.merge(flagged_hr, how='left', on=['Time', 'Heart Rate'])

    # Write the total amount of rows
    summary.write(f"The data has {final_df.shape[0]} rows of data\n\nGAPS FOUND: \n\n")
    for gap in gaps:
        summary.write(gap)

    # Write a summary of the 8pm to 6am data.
    final_row, final_column = final_df.shape
    if end_found:
        sleep_df = final_df.loc[start_index:end_index]
        summary.write("\n8PM TO 6AM Statistics" +
                      "\nFrom 8 to 6 with a 25 samples a second, there should be 900,000 accelerometer readings\n" +
                      "There should be 36,000 heart rate readings from 8 to 6\n")
    else:
        sleep_df = final_df.loc[start_index:end_index]
        summary.write("\nData ends before 6AM." +
                      f"\nSummary runs from 20:00 to {sleep_df.iloc[-1, 0].hour}:{sleep_df.iloc[-1, 0].minute}\n" +
                      f"For a full night you would expect 900,000 accelerometer readings\n" + "For a full night you would expect 36,000 Heart Rate Readings\n")

    # sleep_df['X'] = sleep_df['X'].apply(lambda x: float(x))
    # sleep_df['Y'] = sleep_df['Y'].apply(lambda x: float(x))
    # sleep_df['Z'] = sleep_df['Z'].apply(lambda x: float(x))
    summary.write(sleep_df.describe().to_string())

    # Plotting the the acceleration readings versus time
    print("BEGIN PLOTTING")
    plt.figure(figsize=(25, 15))
    plt.plot(sleep_df['Time'], sleep_df['X'], label="X")
    plt.plot(sleep_df['Time'], sleep_df['Y'], label="Y")
    plt.plot(sleep_df['Time'], sleep_df['Z'], label="Z")
    plt.legend()
    plt.xlim([sleep_start, sleep_end])
    plt.savefig(garmin_path + "\\Processed Data\\" + participant_num + "_xyz.png")
    plt.close('all')

    fig, ax = plt.subplots(figsize=(25, 15))
    hr_helper(final_df, "Garmin", ax, False)
    ax.set(xlim=[sleep_start, sleep_end])
    plt.savefig(garmin_path + "\\Processed Data\\" + participant_num + "_hr.png")
    plt.close('all')

    final_df[['X', 'Y', 'Z']] = final_df[['X', 'Y', 'Z']].apply(pd.to_numeric)
    final_df[['X', 'Y', 'Z']] = final_df[['X', 'Y', 'Z']].apply(lambda x: x / 1000)
    mag, enmo = calc_enmo(final_df.loc[:, ["X", "Y", "Z"]])
    final_df.insert(5, "Magnitude", mag)
    final_df.insert(6, "ENMO", enmo)
    final_df = final_df.loc[(final_df['Time'] >= time[0]) & (final_df['Time'] <= time[1]), :]

    final_df.to_csv(garmin_path + "\\Processed Data\\" + participant_num + "_garmin_data.csv", index=False)
    print("GARMIN PROCESSING FINISHED")
    summary.close()
    return final_df

    # In[ ]:
