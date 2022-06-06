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





# In[4]:


# Convert fit file to csv
def fit_to_csv(fit_path, out_path, part_num):
    jar_path = ".\\processing_scripts\\FitCSVTool.jar"
    count = 1
    for file in fit_path :
        csv_path = out_path + "\\" + part_num + "_" + str(count) + "_raw.csv"
        subprocess.call(['java', '-jar', jar_path, '-b', file, csv_path, '--data', 'record'])

def process_garmin(data_path, garmin_path, participant_num):
    # Read file into a Pandas dataframe
    data = None
    for file in data_path:
        if data is None:
            data = pd.read_csv(file)
        else :
            temp = pd.read_csv(file)
            data = pd.concat([data, temp], ignore_index=True)

    # Convert the Garmin timestamp to the excel number format.
    # Date garmin was founded
    garmin_date = datetime(year=1989, month=12, day=31)
    # Changes depending on Daylight savings
    daylight = input("Is it currently daylight savings time?")
    if daylight.lower() == 'yes':
        offset = timedelta(hours=4)
    else:
        offset = timedelta(hours=5)

    # The Garmin timestamp is the number of seconds that have passed since the founding of Garmin.
    data['record.timestamp[s]'] = data['record.timestamp[s]'].apply(lambda x: timedelta(seconds=x) + garmin_date - offset)

    # Here I create a smaller dataframe with only the readings that we're interested in
    xyz_df = data.loc[:, ['record.timestamp[s]', 'record.developer.0.SensorAccelerationX_HD[mgn]', 'record.developer.0.SensorAccelerationY_HD[mgn]', 'record.developer.0.SensorAccelerationZ_HD[mgn]', 'record.heart_rate[bpm]']]
    # Convert that dataframe to a numpy array for faster iteration
    xyz_numpy = xyz_df.to_numpy()
    rows, columns = xyz_numpy.shape
    # Pre allocate an unpacked array. The reason that it has 50 * the amount of rows than the xyz array is in case
    # The garmin device records more than 25 readings in a  second. I assume here that it would not record any more than
    # 50 readings.
    unpack_xyz = np.zeros((rows*50, columns+1), dtype="O")

    # Initialize counter to keep track of my place in the merged array.
    counter = 0
    # Initialize total to keep track of the total amount of readings in the array
    total = 0
    accel_index = np.arange(1, 51)

    # Iterate through the Garmin array
    for readings in xyz_numpy :    # Check to see if the xyz data is empty
        if pd.isna(readings[1]) :
            unpack_xyz[counter, 0] = readings[0]
            unpack_xyz[counter, 1] = 1
            unpack_xyz[counter, 2:] = readings[1:]

            counter += 1
            total += 1
        else : # The xyz is not empty
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
            unpack_xyz[counter: counter + num_z, 0] = readings[0].strftime("%Y-%m-%d %H:%M:%S")
            # Add assign a number to each acceleration reading numbering 1 to the amount of readings detected.
            unpack_xyz[counter: counter + num_z, 1] = accel_index[0: num_z]

            # Add the heart rate reading to the first acceleration reading.
            unpack_xyz[counter, 5] = readings[4]
            counter += num_x
            total += num_x

    final_df = pd.DataFrame(unpack_xyz[0:total], columns = ['Time', 'Reading #', 'X', 'Y', 'Z', 'Heart Rate'])
    final_df["Heart Rate"] = final_df["Heart Rate"].replace(['0', 0], np.nan)

    # Output data
    output_path = os.path.join(garmin_path, "Processed Data")
    if os.path.isdir(output_path) is False:
        os.mkdir(output_path)

    out_path = output_path + "/" + participant_num + "_garmin.csv"
    final_df.to_csv(out_path, index=False)
    return final_df

