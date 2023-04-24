#!/usr/bin/env python
# coding: utf-8

# ## Welcome
# To begin running the code click the first box of code and then the run button at the top. You will know the code section is done running when their is a nubmer in the square brackets to the left.
# 
# <br><br> The purpose of this script is to upack the Garmin Acceleration Data. Initially the Garmin Accleration data is has 25 readings in one cell corresponding to 1 timestamp. This script unpacks that cell and instead has 1 acceleration reading per row.

# In[1]:


import pandas as pd
import numpy as np
from datetime import datetime
from datetime import timedelta
import subprocess
import os
from .data_summary import calc_enmo, flag_hr


# In[4]:


# Convert fit file to csv
def fit_to_csv(fit_path, out_path, part_num):
    jar_path = "./Protocol_Scripts/processing_scripts/FitCSVTool.jar"
    count = 1
    for file in fit_path:
        csv_path = out_path + "\\" + part_num + "_" + str(count) + "_raw.csv"
        subprocess.call(['java', '-jar', jar_path, '-b', file, csv_path, '--data', 'record'])
        count += 1


def process_garmin(data_path, garmin_path, participant_num, part_age, trial_start, trial_end, protocol="PA"):
    # Read file into a Pandas dataframe
    data = None
    for file in data_path:
        if data is None:
            data = pd.read_csv(file)
        else:
            temp = pd.read_csv(file)
            data = pd.concat([data, temp], ignore_index=True)

    # Convert the Garmin timestamp to the excel number format.
    # Date garmin was founded
    garmin_date = datetime(year=1989, month=12, day=31)

    # The Garmin timestamp is the number of seconds that have passed since the founding of Garmin.
    data['record.timestamp[s]'] = data['record.timestamp[s]'].apply(lambda x: timedelta(seconds=x) + garmin_date)

    # Changes depending on Daylight savings
    date = data.iloc[0, 0]
    if datetime(year=2022, month=3, day=13, hour=2) <= date <= datetime(year=2022, month=11, day=6, hour=2) or \
            datetime(year=2023, month=3, day=12, hour=2) <= date <= datetime(year=2023, month=11, day=5, hour=2) or \
            datetime(year=2024, month=3, day=10, hour=2) <= date <= datetime(year=2024, month=11, day=3, hour=2):
        offset = timedelta(hours=4)
    else:
        offset = timedelta(hours=5)

    data['record.timestamp[s]'] = data['record.timestamp[s]'].apply(lambda x: x - offset)

    # Here I create a smaller dataframe with only the readings that we're interested in
    xyz_df = data.loc[:, ['record.timestamp[s]', 'record.developer.0.SensorAccelerationX_HD[mgn]',
                          'record.developer.0.SensorAccelerationY_HD[mgn]',
                          'record.developer.0.SensorAccelerationZ_HD[mgn]', 'record.heart_rate[bpm]']]
    # Convert that dataframe to a numpy array for faster iteration
    xyz_numpy = xyz_df.to_numpy()
    rows, columns = xyz_numpy.shape
    # Pre allocate an unpacked array. The reason that it has 50 * the amount of rows than the xyz array is in case
    # The garmin device records more than 25 readings in a  second. I assume here that it would not record any more than
    # 50 readings.
    unpack_xyz = np.zeros((rows * 50, columns + 1), dtype="O")

    # Initialize counter to keep track of my place in the merged array.
    counter = 0
    # Initialize total to keep track of the total amount of readings in the array
    total = 0
    accel_index = np.arange(1, 51)

    # Iterate through the Garmin array
    for readings in xyz_numpy:  # Check to see if the xyz data is empty
        if pd.isna(readings[1]) or pd.isna(readings[2]) or pd.isna(readings[3]):
            unpack_xyz[counter, 0] = readings[0] + timedelta(milliseconds=0)
            unpack_xyz[counter, 1] = 1
            unpack_xyz[counter, 2:] = readings[1:]

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
            # unpack_xyz[counter: counter + num_z, 0] = readings[0]
            for i in range(counter, counter + num_z):
                milli_sec = i - counter
                unpack_xyz[i, 0] = readings[0] + timedelta(milliseconds=milli_sec * 40)
            # Add assign a number to each acceleration reading numbering 1 to the amount of readings detected.
            unpack_xyz[counter: counter + num_z, 1] = accel_index[0: num_z]

            # Add the heart rate reading to the first acceleration reading.
            unpack_xyz[counter, 5] = readings[4]
            counter += num_x
            total += num_x

    final_df = pd.DataFrame(unpack_xyz[0:total], columns=['Time', 'Reading #', 'X', 'Y', 'Z', 'Heart Rate'])
    final_df['Time'] = final_df['Time'].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S.%f"))
    final_df["Heart Rate"] = final_df["Heart Rate"].replace(['0', 0], np.nan)

    # Output data
    output_path = os.path.join(garmin_path, "Processed Data")
    if os.path.isdir(output_path) is False:
        os.mkdir(output_path)

    final_df['Time'] = pd.to_datetime(final_df['Time'])
    final_df = final_df.loc[(final_df['Time'] >= trial_start) & (final_df['Time'] <= trial_end), :]

    # Flag HR
    flagged_hr = flag_hr(final_df, "Garmin", part_age, protocol)
    final_df = final_df.merge(flagged_hr, how='left', on=["Time", "Heart Rate"])
    # Calculate vector magnitude and ENMO
    final_df[['X', 'Y', 'Z']] = final_df[['X', 'Y', 'Z']].apply(pd.to_numeric)
    final_df[['X', 'Y', 'Z']] = final_df[['X', 'Y', 'Z']].applymap(lambda x: x / 1000)
    mag, enmo = calc_enmo(final_df.loc[:, ["X", "Y", "Z"]])
    final_df.insert(5, "Magnitude", mag)
    final_df.insert(6, "ENMO", enmo)

    out_path = output_path + "/" + participant_num + "_garmin.csv"
    final_df.to_csv(out_path, index=False)
    return ["Garmin", final_df]


if __name__ == "__main__":
    participant_dir = "C:/Users/Nick/Watch_Extraction/Physical_Activity_Protocol/Test_Data/wearables_v2/7518111722/Garmin/"
    participant_file = [participant_dir + "7518111722_Garmin_0_data.csv"]
    participant_num = "7518111722"
    age = 6
    start = datetime(year=2022, month=11, day=17, hour=21, minute=47)
    end = datetime(year=2022, month=11, day=18, hour=5, minute=17)
    test = process_garmin(participant_file, participant_dir, participant_num, age, start, end, protocol='sleep')

