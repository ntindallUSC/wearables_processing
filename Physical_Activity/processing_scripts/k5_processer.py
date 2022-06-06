#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
from datetime import timedelta


# In[2]:


# Get path to data
root = tk.Tk()
root.winfo_toplevel().title("Select csv files")
root.withdraw()

filepath = filedialog.askopenfilename()
filepath


# # Read in K5 Data
# The first major goal to accomplish is to read in the data and then reformat it to only contain the relevant data and the time of each sampling.

# In[3]:


# Read data
data = pd.read_excel(filepath, header=None)
data


# In[4]:


# Function reads in the timestamps from the data and converts them to time deltas.
# This is needed because python doesn't allow timestamps to be added to datetimes.
def time_to_delta(time) :
    # Makes sure the value is not a string or na
    if not isinstance(time, str) and not pd.isna(time) :
        time = timedelta(hours=time.hour, minutes=time.minute, seconds=time.second)
    return time
# Convert the elapsed time column to timedelta. THis allows for the calculation of recording time, by adding the
# time delta to the start time.
data[9] = data[9].apply(lambda x : time_to_delta(x))


# In[5]:


# Grab the start and end time of the test.
date = data.iloc[0, 4]
time = data.iloc[1, 4]
# Combine start date and time.
start = date + " " + time
start_time = datetime.strptime(start, '%m/%d/%Y %I:%M %p')
print(f"Start Time: {start_time}")
# Grab duration of test from table
duration = data.iloc[2,4]
print(f"Test Duration: {duration}")
# Add duration + startime to get end time
end_time = start_time + timedelta(hours=duration.hour, minutes=duration.minute, seconds=duration.second)
print(f"End Time {end_time}")


# In[6]:


# Drop beginning columns that hold no data
data.drop(columns=[0,1,2,3,4,5,6,7,8], inplace=True)
data.drop(index=[1], inplace=True)

# Drop empty columns
data.dropna(axis=0, how='all', inplace=True)

# Make first row the headers of dataframe
data.columns = data.iloc[0,:]
data.drop(index=0, inplace=True)
data


# In[7]:


# Convert elapsed time column to a column that contains timestamps of when data was collected
def timestamp(elapse, start) :
    # Make sure the value is a time
    if isinstance(elapse, timedelta) :
        elapse = elapse + start
    return elapse
data['t'] = data['t'].apply(lambda x : timestamp(x, start_time))


# In[8]:


data


# # Read In Activity Labels
# The next major goal to accomplish is to add activity labels to the data. Essentially for each timestamp we want to know that activity the child was performing. Before doing this, I first must read in the activity log and determine the start and end time of each activity.

# In[9]:


# First I need to read in the activity log
log_path = filedialog.askopenfilename()
log_path


# In[10]:


log = pd.read_excel(log_path)
log


# In[11]:


# This creates a dictionary of tuples.
# Each tuple contains the name of activity, start time, and end time
activities = {}
for i in range(log.shape[0]) :
    # Get name of the activity
    name = log.iloc[i, 0]
    # Get start time of activity
    acti_start = date + " " + str(log.iloc[i,1])
    acti_start = datetime.strptime(acti_start, '%m/%d/%Y %H:%M:%S')
    # Get end time of activity
    acti_end = date + " " + str(log.iloc[i,2])
    acti_end = datetime.strptime(acti_end, '%m/%d/%Y %H:%M:%S')
    # Create Tuple
    activity = (name, acti_start, acti_end)
    # Add to dictionary
    activities[str(i + 1)] = activity
activities


# # Label K5 Data
# Now that I have the K5 data timestamped and the time of each activity, I need to label all the data based on activity.

# In[12]:


# Here I insert a column into my K5 data.
# This column will hold the names of activites
data.insert(1, "Activity", "Break", True)


# In[13]:


# Here I iterate through my dictonary, accessing each activty
acti_num = 1
for acti in activities:
    # Get the tuple of activity information
    acti = activities[acti]
    # Select each row from data who's timestamp falls during and activtiy and then change the activity column to that 
    # activity name
    #       **************Selecting Rows******************  Grab a column -> Set equal to name
    data.loc[(data['t'] >= acti[1]) & (data['t'] < acti[2]), 'Activity'] = acti[0]
data


# # Write data to file
# 

# In[14]:


outpath = filedialog.askdirectory()
outpath


# In[15]:


data.to_csv(outpath + "/962_labled_K5_02.csv", index=False)


# In[ ]:




