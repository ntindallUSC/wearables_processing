#!/usr/bin/env python
# coding: utf-8

# In[8]:


import pandas as pd
import os
import datetime
import numpy as np


# ## Read in the PSG Data
# This subsection of code reads in the sample PSG file. Right now I have the explicit path hard coded in. Later once we have a real version I'll replace it.

# In[9]:

def psg_process(participant_num, psg_path, psg_summary, psg_data, start, end):

    # Just try to read in the PSG file for now.
    file_path = psg_data
    new_path = psg_path + participant_num + "ebe_no_head.txt"

    original = open(file_path, mode='r')
    no_head = open(new_path, mode='w')

    head_count = 0
    # This for loop reads through the psg file and writes just the data to a new file.
    # Essentially removing the header of the file and extra column names

    for line in original:
        if line[0] == "#":
            head_count += 1

        if head_count > 0:
            if line[0] != '#' or head_count == 1:
                no_head.write(line)

    original.close()
    no_head.close()

    # In[12]:

    psg = pd.read_csv(new_path, delimiter=' ', skipinitialspace=True, low_memory=False)
    os.remove(new_path)
    psg = psg[['#', 'BP', "Stg"]]

    # # Timestamp the PSG Data Currently the PSG data only has an epoch number. In a separate file it's the time of
    # lights out is recorded. Each epoch is 30 seconds. I can use this time to assign a time value to each epoch.

    # In[14]:

    # First I need to read in the file with the lights out time stamp.
    file_path = psg_summary

    # # Find time of lights out
    # The code below gets the date and time of lights out. I do this by searching the summary psg file for certain key phrases

    # In[18]:

    file = open(file_path, 'r')
    line = file.readline()
    # Get date from file name:
    #               Month                           Day                     Year
    date = participant_num[-6:-4] + "/" + participant_num[-4:-2] + "/20" + participant_num[-2:]
    # Search for the spot in the file where they begin to list the time of sleep
    while "sleep overview" not in line.casefold():
        line = file.readline()
    if len(line) == 0:
        line = file.readline()
    # The line following sleep summary is the time that the lights were turned off.
    time_out = file.readline()[-9:].strip()
    file.close()
    # print(date)
    ref_time = datetime.datetime.strptime(date + time_out, '%m/%d/%Y%H:%M:%S')
    if 0 <= ref_time.hour <= 6:
        ref_time += datetime.timedelta(hours=24)
    # print(f"Lights out at {ref_time}")

    # In[19]:

    # The line of code below gets the index value of the last epoch before the lights were switched off.
    out_index = psg.Stg.ne('L').idxmax()
    psg.iloc[out_index]

    # # Create timestamp for each epoch
    # The following code will generate a list of timestamps that correspond to each epoch of psg

    # In[20]:

    # Now I need declare the length of the epoch and add
    epoch_len = datetime.timedelta(seconds=30)
    epoch_num = psg.shape[0]

    # Declare a data structure to hold all of the psg readings and time stamp
    psg_np = psg.to_numpy()
    timestamped_psg = []

    # Use a for loop to add entries before lights out
    for i in range(out_index):
        new_time = ref_time - (out_index - i) * epoch_len
        timestamped_psg.append([new_time, psg_np[i, 0], psg_np[i, 1], psg_np[i, 2]])

    # Use a for loop to add the entries after the time went out
    # Count counts how many epochs have passed since the lights went out
    count = 0
    for i in range(out_index, epoch_num):
        new_time = ref_time + count * epoch_len
        timestamped_psg.append([new_time, psg_np[i, 0], psg_np[i, 1], psg_np[i, 2]])
        count += 1

    psg_final = pd.DataFrame(timestamped_psg, columns=['Time', 'Epoch #', "BP", "Stg"])
    psg_final = psg_final.loc[(psg_final['Time'] >= start) & (psg_final['Time'] <= end), :]

    file_path = psg_path + participant_num + "_time_stamped.csv"
    psg_final.to_csv(file_path, index=False)
    return ["PSG", psg_final]

# In[ ]:
