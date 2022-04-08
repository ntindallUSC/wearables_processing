#!/usr/bin/env python
# coding: utf-8

# ## Welcome
# To begin running the code click the first box of code and then the run button at the top. You will know the code section is done running when their is a nubmer in the square brackets to the left.
# 
# <br><br> The purpose of this script is to upack the Garmin Acceleration Data. Initially the Garmin Accleration data is has 25 readings in one cell corresponding to 1 timestamp. This script unpacks that cell and instead has 1 acceleration reading per row.

# In[2]:
import datetime

import pandas as pd
import numpy as np
import xlrd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# In[3]:


def garmin_process(participant_num, garmin_path, csv_data):
    print("BEGIN GARMIN PROCESSING")
    # Open summary file to write to.
    summary_path = garmin_path + "\\Processed Data\\" + participant_num + "_garmin_summary.txt"
    summary = open(summary_path, 'w')
    summary.write(f"Participant {participant_num} Summary\n")
    # Read file into a Pandas dataframe
    gaps = []
    num_files = 0
    for file in csv_data:
        # Checks if the file being read in is the first file
        if num_files == 0:
            data = pd.read_csv(file)
        else:
            # read in next file
            temp = pd.read_csv(file)
            # Find the gap start and end, then convert to time and store in gaps list
            gap_start = (data.iloc[-1,0] / 60 / 60 / 24) + 32872.79166666670
            gap_start = xlrd.xldate_as_datetime(gap_start, 0)
            gap_end = (temp.iloc[0,0] / 60 / 60 / 24) + 32872.79166666670
            gap_end = xlrd.xldate_as_datetime(gap_end, 0)
            gaps.append(f"Gap found between {gap_start} and {gap_end}\n")
            # combine two files
            data = pd.concat([data, temp], ignore_index=True)
        num_files += 1

    # In[4]:
    # Convert the Garmin timestamp to the excel number format.
    # The Garmin timestamp is the number of seconds that have passed since the founding of Garmin.
    data['record.timestamp[s]'] = data['record.timestamp[s]'].apply(lambda x: (x / 60 / 60 / 24) + 32872.79166666670)


    # In[5]:

    # Here I create a smaller dataframe with only the readings that we're interested in
    xyz_df = data.loc[:, ['record.timestamp[s]', 'record.developer.0.SensorAccelerationX_HD[mgn]',
                          'record.developer.0.SensorAccelerationY_HD[mgn]',
                          'record.developer.0.SensorAccelerationZ_HD[mgn]', 'record.heart_rate[bpm]']]
    # Convert that dataframe to a numpy array for faster iteration
    xyz_numpy = xyz_df.to_numpy()
    rows, columns = xyz_numpy.shape
    start = xlrd.xldate_as_datetime(data.iloc[0,0], 0)
    end = xlrd.xldate_as_datetime(data.iloc[-1,0], 0)
    # Write start tiem and end time and number of rows to summary file
    summary.write(f"Start Time: {start} \nEnd Time: {end}\n")
    summary.write(f"The Garmin data intially had {rows} rows of data.\n" +
                  "Each row of data should have 1 heart rate reading and 25 accelerometer readings.\n" +
                  f"In total there would be {rows*25} rows after unpacking\n")


    # Pre allocate an unpacked array. The reason that it has 50 * the amount of rows than the xyz array is in case
    # The garmin device records more than 25 readings in a  second. I assume here that it would not record any more than
    # 50 readings.
    unpack_xyz = np.zeros((rows * 50, columns + 1))

    # In[13]:

    # Initialize counter to keep track of my place in the merged array.
    counter = 0
    # Initialize total to keep track of the total amount of readings in the array
    total = 0
    accel_index = np.arange(1, 51)

    # initialize variables to help find 8pm and 6am in the data set.
    # I need these time values so I can write a summary on the data for this time set.
    #               Year                                Month                       Day
    date = (int("20"+participant_num[-2:]), int(participant_num[-6:-4]), int(participant_num[-4:-2]))
    sleep_start = datetime.datetime(year=date[0], month=date[1], day=date[2], hour=20)
    start_found = False
    start_index = 0
    sleep_end = datetime.datetime(year=date[0], month=date[1], day=date[2], hour=8) + datetime.timedelta(days=1)
    end_found = False
    end_index = 0

    abnormal_hr = 0
    # Iterate through the Garmin array
    for readings in xyz_numpy:  # Check to see if the xyz data is empty
        # print(xlrd.xldate_as_datetime(readings[0], 0).hour)
        if xlrd.xldate_as_datetime(readings[0], 0) >= sleep_start and start_found is False:
            start_index = counter
            start_found = True
        if start_found is True and xlrd.xldate_as_datetime(readings[0], 0) <= sleep_end and end_found is False:
            end_index = counter
            if xlrd.xldate_as_datetime(readings[0], 0) == sleep_end :
                end_found = True

        if pd.isna(readings[1]):
            unpack_xyz[counter, 0] = readings[0]
            unpack_xyz[counter, 1] = 1
            unpack_xyz[counter, 2:] = readings[1:]

            counter += 1
            total += 1
        else:  # The xyz is not empty
            # Get the amount of accleration readings in the x, y, and z direction
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


    # Write the total amount of rows
    summary.write(f"The data has {final_df.shape[0]} rows of data\n\nGAPS FOUND: \n\n")
    for gap in gaps:
        summary.write(gap)


    # In[14]:

    # Here I convert the first column excel number to an easy to understand date and time
    final_df['Time'] = final_df['Time'].apply(lambda x: str(xlrd.xldate_as_datetime(x, 0)))
    final_df['Time'] = pd.to_datetime(final_df['Time'])
    final_row,final_column = final_df.shape

    # In[15]:
    # Write a summary of the 8pm to 6am data.
    if end_found:
        sleep_df = final_df.iloc[start_index:end_index]
        summary.write("\n8PM TO 6AM Statistics" +
                      "\nFrom 8 to 6 with a 25 samples a second, there should be 900,000 accelerometer readings\n" +
                      "There should be 36,000 heart rate readings from 8 to 6\n")
    else:
        sleep_df = final_df.iloc[start_index:final_row - 1]
        summary.write("\nData ends before 6AM." +
                      f"\nSummary will run from 8pm to {sleep_df.iloc[-1,0].hour}\n" +
                      f"You should expect {(8 - int(sleep_df.iloc[-1,0].hour)) * 25 * 60 *60} accelerometer readings\n")

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

    plt.figure(figsize=(25, 15))
    # Need to drop the readings without a heart rate before plotting
    thin_time = sleep_df[['Time', 'Heart Rate']].dropna(axis=0)
    plt.plot(thin_time['Time'], thin_time['Heart Rate'])
    plt.xlim([sleep_start, sleep_end])
    plt.savefig(garmin_path + "\\Processed Data\\" + participant_num + "_hr.png")

    final_df.to_csv(garmin_path + "\\Processed Data\\" + participant_num + "_garmin_data.csv", index=False)
    print("GARMIN PROCESSING FINISHED")
    summary.close()

    # In[ ]:
