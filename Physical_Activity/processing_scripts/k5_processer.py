#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
from datetime import datetime
from datetime import timedelta
import os


def process_k5(k5_path, log_path, folder_path, participant_num):
    data = None
    for file in k5_path:
        # # Read in K5 Data
        temp = pd.read_excel(file, header=None)

        # Function reads in the timestamps from the data and converts them to time deltas.
        # This is needed because python doesn't allow timestamps to be added to datetimes.
        def time_to_delta(time):
            # Makes sure the value is not a string or na
            if not isinstance(time, str) and not pd.isna(time):
                time = timedelta(hours=time.hour, minutes=time.minute, seconds=time.second)
            return time

        # Convert the elapsed time column to timedelta. THis allows for the calculation of recording time, by adding the
        # time delta to the start time.
        temp[9] = temp[9].apply(lambda x: time_to_delta(x))

        # Grab the start and end time of the test.
        date = temp.iloc[0, 4]
        time = temp.iloc[1, 4]
        # Combine start date and time.
        start = date + " " + time
        start_time = datetime.strptime(start, '%m/%d/%Y %I:%M %p')
        # print(f"Start Time: {start_time}")
        # Grab duration of test from table
        duration = temp.iloc[2, 4]
        # print(f"Test Duration: {duration}")
        # Add duration + startime to get end time
        end_time = start_time + timedelta(hours=duration.hour, minutes=duration.minute, seconds=duration.second)
        # print(f"End Time {end_time}")

        # Drop beginning columns that hold no data
        temp.drop(columns=[0, 1, 2, 3, 4, 5, 6, 7, 8], inplace=True)
        temp.drop(index=[1], inplace=True)

        # Drop empty columns
        temp.dropna(axis=0, how='all', inplace=True)

        # Make first row the headers of dataframe
        temp.columns = temp.iloc[0, :]
        temp.drop(index=0, inplace=True)

        # Convert elapsed time column to a column that contains timestamps of when data was collected
        def timestamp(elapse, start):
            # Make sure the value is a time
            if isinstance(elapse, timedelta):
                elapse = elapse + start
            return elapse

        temp['t'] = temp['t'].apply(lambda x: timestamp(x, start_time))
        temp['t'] = pd.to_datetime(temp['t'])

        # # Read In Activity Labels
        log = pd.read_excel(log_path[0])
        # This creates a dictionary of tuples.
        # Each tuple contains the name of activity, start time, and end time
        activities = {}
        for i in range(log.shape[0]):
            # Get name of the activity
            name = log.iloc[i, 0]
            # Get start time of activity
            acti_start = date + " " + str(log.iloc[i, 1])
            acti_start = datetime.strptime(acti_start, '%m/%d/%Y %H:%M:%S')
            # Get end time of activity
            acti_end = date + " " + str(log.iloc[i, 2])
            acti_end = datetime.strptime(acti_end, '%m/%d/%Y %H:%M:%S')
            # Create Tuple
            activity = (name, acti_start, acti_end)
            # Add to dictionary
            activities[str(i + 1)] = activity

        # # Label K5 Data
        # Now that I have the K5 data timestamped and the time of each activity, I need to label all the data based on activity.
        # Here I insert a column into my K5 data.
        # This column will hold the names of activities
        temp.insert(1, "Activity", "Transition", True)
        temp.loc[(temp['t'] < activities['1'][1]), "Activity"] = "Before Protocol"
        temp.loc[(temp['t'] >= activities[str(len(activities))][2]), "Activity"] = "After Protocol"

        # Here I iterate through my dictionary, accessing each activity
        for acti in activities:
            # Get the tuple of activity information
            acti = activities[acti]
            # Select each row from data who's timestamp falls during and activity and then change the activity column to that
            # activity name
            #       **************Selecting Rows******************  Grab a column -> Set equal to name
            temp.loc[(temp['t'] >= acti[1]) & (temp['t'] < acti[2]), 'Activity'] = acti[0]
        if data is None:
            data = temp
        else:
            data = pd.concat([data, temp], ignore_index=True)

    # Write data to a csv
    output_path = os.path.join(folder_path, "Processed Data")
    if os.path.isdir(output_path) is False:
        os.mkdir(output_path)

    output_file = output_path + '/' + participant_num + '_k5.csv'

    data.to_csv(output_file, index=False)
    return data, activities
