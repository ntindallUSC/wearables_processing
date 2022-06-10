#!/usr/bin/env python
# coding: utf-8

# # Welcome!
# To begin running the code you must click the top left portions of each block of code. When you hover over each code's top left corner a play button should appear. Clicking this will execute that block of code. Please be sure to run the code sequentially from the top of the page to the bottom of the page.
# 
# This first little bit of code imports some packages that I will be using throughout the rest of my code. 

# In[ ]:


import numpy as np
from datetime import datetime
from datetime import timedelta
import pandas as pd
import matplotlib.pyplot as plt


# ## First you need to load the data into the script
# 
# When you run the code block below a file window should open. First you need to select the Sensorlog file that you
# wish to process. After that select the Auto Health File you wish to process.
# 
# Note you may need to minimize the Jupyter notebook window to see the file selection screen.

# In[ ]:

def apple_process(participant_num, apple_path, sensor_log, auto_health):
    print("BEGIN APPLE PROCESSING")
    summary = open(apple_path + "\\Processed Data\\Apple_Summary.txt", 'w')
    # delim is True if the document is comma separated:
    delim = True
    cur_file = 0
    for file1 in sensor_log:

        # Peek at the file to see if it is comma delimited or pipe delimited
        test = open(file1, 'r')
        line = test.readline()
        for char in line:
            if char == "|":
                delim = False
                break
            elif char == ",":
                break
        test.close()

        # If it's the first file read in create the accel dataframe and read in the csv file
        if cur_file == 0:
            if delim:
                accel = pd.read_csv(file1)
            else:
                accel = pd.read_csv(file1, delimiter='|')
        # Read in a file and append it to the accel data frame
        else:
            if delim:
                temp = pd.read_csv(file1)
            else:
                temp = pd.read_csv(file1, delimiter='|')
            accel = pd.concat([accel, temp], ignore_index=True)
        cur_file += 1

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

    # In[ ]:

    # Read in the heart rate file
    heart = pd.read_csv(auto_health[0])

    # Here I convert the data type in time column in the heart rate data to a timestamp
    heart['Date/Time'] = pd.to_datetime(heart['Date/Time'])
    # print(heart)

    # In[ ]:

    # Get the shape of the accel and heart datafame. I will use these later
    a_row, a_column = accel.shape
    h_row, h_column = heart.shape
    summary.write(f"Began recording at {accel.iloc[0,0]}\n")
    summary.write(f"Ended recording at {accel.iloc[-1,0]}\n")

    summary.write(f"The Accelerometer file has {a_row} rows in total\n")
    summary.write(f"The Heartrate file has {h_row} rows in total\n")

    # Convert the accel and heart dataframes to numpy arrays.
    # It's faster to iterate through numpy arrays than pandas dataframes.
    accel_np = accel.to_numpy()
    heart_np = heart.to_numpy()

    # ## Process the data In this section of code I iterate through both the heart rate files and the acceleration
    # files and add them to my merged array. I look at 2 adjacent acceleration readings and compare the times of
    # recording to the time of recording of a single heart rate. There are 3 cases to consider here:<br> <br>1. The
    # heart rate time stamp is less than both of the acceleration time stamps.<br> <br>2. The heart rate time stamp
    # is in between two inbetween or equal to the accleration time stamps.<br> <br>3. The heart rate time stamp is
    # greater than both of my acceleration time stamps.<br>
    #
    # <br> Case 1 only occurs when I first begin reading the iterating through the entries. If the heart rates occur
    # before the acceration data I iterate through the array until I find a heart rate timestamp that begins after
    # the acceleration readings.<br>
    #
    # <br> Case 2 can be caused by two different scenarios. <br>The first scenario is the heart rate timestamp falls
    # in between 2 adjacent acceleration readings. If this is the case I take the difference between the heart rate
    # timestamp with both of the acceleration timestamps. I then put the heart rate in the row with the acceleration
    # time stamp it is closer to. <br>The second scenario means that their is a gap in the acceleration data. If this
    # occurs there coud potentially be mutliple heart rate readings in the gap.  I check for this by taking the
    # difference between the two acceleration timestamps. If difference is greater than a second I assume that their
    # is a gap. I then add each heart rate reading that occurs in the gap to  the array without any acceleration
    # data.<br>
    #
    # <br>Case 3 occurs when 2 adjacent acceleration readings occur before a heart rate reading. I handle this by
    # adding the 1st  acceleration reading to the array and then check the next 2 adjacent readings.<br>
    #
    #
    #

    # In[ ]:

    # Here I intialize the numpy array that will hold both heart rate and acceleration data
    # I make the # of rows in this array equal to the amount of rows the sum of the acceleration data
    # and heart rate data. I do this because if for some reason there isn't any overlap in time between
    # The two data sets the data structure could hold all of the information.
    merged = np.empty((a_row + h_row, 5), dtype="object")

    # Intialize counters that will be used to iterate through arrays
    h_counter = 0

    # Iterate through heart file until we've reached a reading that corresponds with the first accelerometer reading
    a_reading = accel_np[0]
    h_reading = heart_np[h_counter]
    h_counter += 1

    while h_reading[0] < a_reading[0]:
        h_reading = heart_np[h_counter]
        h_counter += 1

    # In[ ]:

    # Now iterate through both arrays
    flag = 0
    a_second = np.timedelta64(1, 's')
    # I represents the location in the acceleration data
    i = 0
    # j represents the location in the merged array
    j = 0

    # Create two variables to help determine the indices where 8 pm and 6 am occur.
    date = (int("20"+participant_num[-2:]), int(participant_num[-6:-4]), int(participant_num[-4:-2]))
    sleep_start = False
    s_start_time = datetime(year=date[0], month=date[1], day=date[2], hour=20)
    start_index = 0
    sleep_end = False
    s_end_time = datetime(year=date[0], month=date[1], day=date[2], hour=6) + timedelta(days=1)
    end_index = 0

    # Create a variable to keep track of abnomral heart rates:
    abnormal_counter = 0
    # print(f"Beginning Heartrate: {h_reading[0]} \nBeginning Accelerometer {a_reading[0]} \nBegin H counter {h_counter}\n")
    summary.write("\nAcceleration Gaps:\n")
    while i < a_row - 2:

        if accel_np[i + 1, 0] - accel_np[i, 0] > a_second:
            summary.write(f"Gap found between {accel_np[i, 0]} and {accel_np[i + 1, 0]}\n")

            merged[j, 0] = accel_np[i, 0]
            merged[j, 1:4] = accel_np[i, 2:5]

            while accel_np[i + 1, 0] > h_reading[0] and h_counter < h_row:
                if 40 > h_reading[1] or 150 < h_reading[1]:
                    abnormal_counter += 1
                #print(f"{h_reading[0]} is in the gap")
                merged[j, :] = [h_reading[0], np.nan, np.nan, np.nan, h_reading[1]]
                j += 1

                # Add Time and Accelormeter readings to current row
                h_reading = heart_np[h_counter]
                h_counter += 1

        # print(f"Gap found between {accel_np[i,0]} and {accel_np[i+1,0]})")
        merged[j, 0] = accel_np[i, 0]
        merged[j, 1:4] = accel_np[i, 2:5]

        # Use these if statements to check if the time is 8pm
        if accel_np[i, 0] >= s_start_time and sleep_start is False:
            # print(accel_np[i, 0])
            sleep_start = True
            start_index = j

        if sleep_start is True and accel_np[i, 0] <= s_end_time and sleep_end is False:
            #print(accel_np[i,0])
            end_index = j
            if accel_np[i,0] == s_end_time:
                sleep_end = True

        # Checks to see if heart rate should be added from previous comparison
        if flag == 1:
            # print("I'm in the flag")
            # print(f"Check row {i}")
            merged[j, 4] = h_reading[1]
            # print(merged[i])
            flag = 0
            if h_counter >= h_row:
                h_reading = None
            else:
                h_reading = heart_np[h_counter]
                h_counter += 1
                # print(f"Next heartrate time {h_reading[0]} \nNext H_counter {h_counter}\n")

        # Compare accel times
        if h_counter < h_row and (accel_np[i, 0] <= h_reading[0] < accel_np[i + 1, 0]):
            if 40 > h_reading[1] or 150 < h_reading[1]:
                abnormal_counter += 1
            # print(f"Current accel {accel_np[i,0]} \nNext accel {accel_np[i+1,0]}")
            # print(f"Current reading: {h_reading[0]}\n")

            # Get the absolute difference between the 2 accel times and heart time
            diff1 = abs(accel_np[i, 0] - h_reading[0])
            diff2 = abs(accel_np[i + 1, 0] - h_reading[0])

            # Compare to decide which time the heart rate should be paired with
            if diff1 < diff2 or diff1 == 0:
                # print(f'Heart rate at time: {h_reading[1]}')
                # print(f"Check row {i}")
                merged[j, 4] = h_reading[1]
                # print(merged[i])
                if h_counter == h_row:
                    h_reading = None
                else:
                    h_reading = heart_np[h_counter]
                    h_counter += 1


            else:
                # print("I'm in the correct spot")
                flag = 1
        i += 1
        j += 1

    merged[j, 0] = accel_np[a_row - 1, 0]
    merged[j, 1:4] = accel_np[a_row - 1, 2:5]
    if flag == 1:
        merged[j, 4] = h_reading[h_counter, 1]
    j += 1
    while h_counter < h_row :
        merged[j, :] = [heart_np[h_counter, 0], np.nan, np.nan, np.nan, heart_np[h_counter, 1]]
        j += 1
        h_counter += 1

    # In[ ]:

    # Convert the merged numpy array to a Pandas dataframe. I do this to make it easier to output as a csv
    final_df = pd.DataFrame(merged, columns=['Time', 'X', 'Y', 'Z', 'Heart Rate'])

    # Here I grab the data from 8pm to 6am of the
    """
    print(f"Start time: {sleep_start}")
    print(f"End Time: {sleep_end}")
    accel_sleep = accel.iloc[sleep_start:sleep_end]
    accel_sleep_row, accel_sleep_column = accel_sleep.shape
    summary.write(f"Number of accel readings between 8pm and 6am: {accel_sleep_row}")
    """

    # In[ ]:

    # I change all the zero values in the heart rate column to NaNs
    final_df["Heart Rate"] = final_df["Heart Rate"].replace(['0', 0], np.nan)
    final_df['X'] = pd.to_numeric(final_df['X'])
    final_df['Y'] = pd.to_numeric(final_df['Y'])
    final_df['Z'] = pd.to_numeric(final_df['Z'])

    # Here I write general statistics about the data to a summary file.
    final_sleep = final_df.iloc[start_index:end_index]
    # print(f"Start index : {start_index} \nEnd index : {end_index}")
    # print(f"Final Sleep {final_sleep}")
    # print(f"Sleep start {final_sleep.iloc[0,0]} \nSleep end{final_sleep.iloc[-1,0]}")
    final_sum = final_sleep.describe()
    summary.write(f"\nNumber of abnormal heart rate readings: {abnormal_counter}")
    summary.write("\n8PM TO 6PM STATISTICS \n\n")
    summary.write("For 10 hours while sampling at 50 hz we should have 1,800,000 accelerometer readings\n")
    summary.write("For 10 hours with a reading every 5 seconds we should have 7,200 heart rate readings\n")
    summary.write(final_sum.to_string())
    # In[ ]:

    final_df.drop(final_df.iloc[j:].index, inplace=True)

    # In[ ]:

    # In[ ]:

    # ## Create new CSV File
    # Running this code creates a new CSV

    # In[ ]:

    file_name = participant_num + "_apple_data.csv"
    final_df.to_csv(apple_path + "\\Processed Data\\" + file_name, index=False)
    summary.close()

    # Plot the x, y, z data between 8pm and 6am
    print("BEGIN PLOTTING")
    plt.figure(figsize=(25, 15))
    plt.plot(final_sleep['Time'], final_sleep['X'], label="X")
    plt.plot(final_sleep['Time'], final_sleep['Y'], label="Y")
    plt.plot(final_sleep['Time'], final_sleep['Z'], label="Z")
    plt.legend()
    plt.xlim([s_start_time, s_end_time])
    plt.savefig(apple_path + "\\Processed Data\\" + participant_num + "_xyz.png")

    plt.figure(figsize=(25, 15))
    # Need to drop the readings without a heart rate before plotting
    heart_plot_df = final_df.loc[(final_df['Time'] >= s_start_time) & (final_df['Time'] <= s_end_time), ['Time', 'Heart Rate']]
    thin_time = heart_plot_df[['Time', 'Heart Rate']].dropna(axis=0)
    plt.plot(thin_time['Time'], thin_time['Heart Rate'])
    # plt.show()
    plt.xlim([s_start_time, s_end_time])
    plt.savefig(apple_path + "\\Processed Data\\" + participant_num + "_hr.png")
    print("APPLE PROCESSING FINISHED")

    # In[ ]:
