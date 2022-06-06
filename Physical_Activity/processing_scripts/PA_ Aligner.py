#!/usr/bin/env python
# coding: utf-8

# In[19]:


import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog
from datetime import datetime, timedelta
import math


# # Read in data
# There are 5 streams of data that must be read in:
# 1. Actigraph (Acceleration sampled at 100 hz)
# 2. Garmin (Heart rate sampled at 1 hz. Acceleration sampled at 25 hz)
# 3. Apple Watch (Heart rate sampled about every 5 seconds. Accleration sampled at 50 hz)
# 4. ActiHeart (Acceleration sampled at 50 hz. ECG sampled at 256 Hz)
# 5. K5 (Sampled about every 5 seconds)

# In[2]:


# Intialize tk dialog. This is needed to ask user to select files
root = tk.Tk()
root.winfo_toplevel().title("Select csv files")
root.withdraw()

# Get path to folder of participant data
participant_path = filedialog.askdirectory()
participant_path


# In[4]:


# Read in actigraph data 
# First define a date parser. This parser allows the actigraph date format to be converted to pandas timestamp
acti_date_parser  = lambda x: datetime.strptime(x, '%m/%d/%Y %H:%M:%S.%f')
# Read in file and store it as a dataframe. 
actigraph_data = pd.read_csv(participant_path + '/ActiGraph data/csv/1991_acti.csv', skiprows=10, nrows=2000000, 
                             parse_dates=['Timestamp'], date_parser=acti_date_parser)
sec_frac = actigraph_data["Timestamp"].apply(lambda x: x.microsecond)
actigraph_data.insert(1,'Second Fraction', sec_frac)
actigraph_data


# In[5]:


# Read in garmin data
garmin_data = pd.read_csv(participant_path + "/Garmin Data/Processed Data/1991_garmin.csv", parse_dates=['Time'], 
                          infer_datetime_format=True)
garmin_data


# In[6]:


# Read in Apple Watch Data
apple_data = pd.read_csv(participant_path + "/Apple Data/Processed Data/1991_apple.csv", parse_dates=["Time"],
                        infer_datetime_format=True)
apple_data


# In[8]:


# Read in Actiheart Data
actiheart_data = pd.read_csv(participant_path + "/Actiheart data/Processed Data/1991_actiheart.csv", parse_dates=['ECG Time'],
                            infer_datetime_format=True)
actiheart_data


# In[9]:


# Read in K5 data
k5_data = pd.read_csv(participant_path + "/K5 data/Processed_Data/1991_labled_K5.csv", parse_dates=['t'], 
                      infer_datetime_format=True )
k5_data


# # Align Data
# Now that the data has been read in the next step is to align the all of the data. Here are the steps to do this:
# 1. Convert all the dataframes to numpy arrays for faster iteration
# 2. Throw away readings sampled before the start of the trial. (The k5 started recording when the trial started.)
# 3. Align all data. (Done be iterating through the actiheart file and adding the other device readings to the closest row.)

# In[10]:


# Convert all 5 data frames to numpy arrays
graph_np = actigraph_data.to_numpy()
garmin_np = garmin_data.to_numpy()
apple_np = apple_data.to_numpy()
heart_np = actiheart_data.to_numpy()
k5_np = k5_data.to_numpy()


# In[11]:


# Get dimensions of each array. These will be needed for boundary checking.
graph_rows, graph_cols = graph_np.shape
garmin_rows, garmin_cols = garmin_np.shape
apple_rows, apple_cols = apple_np.shape
heart_rows, heart_cols = heart_np.shape
k5_rows, k5_cols = k5_np.shape


# In[12]:


# Intialize trial start and end
t_start = k5_np[0,0] - timedelta(seconds=k5_np[0,0].second)
t_end = k5_np[-1,0]

# intialize device iterators and iterate to start of trial
# actigraph
graph_iter = 0
while graph_np[graph_iter,0] < t_start :
    graph_iter += 1

# garmin
garmin_iter = 0
while garmin_np[garmin_iter, 0] < t_start :
    garmin_iter += 1

# apple
apple_iter = 0
while apple_np[apple_iter, 0] < t_start :
    apple_iter += 1

# actiheart
heart_iter = 0
while heart_np[heart_iter,0] < t_start :
    heart_iter += 1

# k5
k5_iter = 0

# Initialize out_np (The aligned output array)
out_rows = k5_rows * 3 * 256 # K5 has 1 reading about every 3 seconds, actiheart is collecting 256 readings a second. 
out_cols = graph_cols + garmin_cols + apple_cols + heart_cols + k5_cols # Sum of all device columns
out_np = np.zeros([out_rows, out_cols], dtype="O") # Intilize Array
out_iter = 0 # Intialize output iterator


# In[13]:


# Function that compares 1 device reading with 2 consecutive actiheart  readings and adds then adds to output row
# Depending on whether the reading occured
def reading_check(device_np, device_iter, device_rows, device_cols) :
    # Get out_row, and actiheart info
    global out_row
    global heart_np
    global heart_iter
    
    # Check if device reading has occured:
    #   Boundary Checking          Check if current device reading occurs between 2 consecutive actiheart readings
    if device_iter < device_rows and (heart_np[heart_iter, 0] <= device_np[device_iter, 0] < heart_np[heart_iter + 1, 0] 
                                     or heart_np[heart_iter, 0] > device_np[device_iter, 0]) :
        
        # Check which actiheart reading is closer to the device reading:
        if abs(heart_np[heart_iter, 0] - device_np[device_iter, 0]) <= abs(heart_np[heart_iter + 1, 0] - device_np[device_iter, 0]):
            for value in device_np[device_iter, :] :
                out_row.append(value)
                # Move to next actigraph reading
            device_iter += 1
        else :
            for i in range(device_cols) :
                out_row.append(np.nan)

    else : # No device reading occured
        for i in range(device_cols):
            out_row.append(np.nan)
    
    return device_iter
    


# In[14]:


# Begin alignment
while heart_iter < heart_rows - 1 and heart_np[heart_iter - 1, 0] < t_end:
    # Intialize out_row as empty row. Throught loop data will be added to row and then row will be added to output array.
    out_row = []
    
    # Add actiheart data
    for value in heart_np[heart_iter, :] :
        out_row.append(value)
    
    # check if actigraph reading has occured
    graph_iter = reading_check(graph_np, graph_iter, graph_rows, graph_cols)
    # check if garmin reading has occrured
    garmin_iter = reading_check(garmin_np, garmin_iter, garmin_rows, garmin_cols)
    # check if apple reading has occured
    apple_iter = reading_check(apple_np, apple_iter, apple_rows, apple_cols)
    # check if k5 reading has occured
    k5_iter = reading_check(k5_np, k5_iter, k5_rows, k5_cols)
    
        
    # Add out_row to out_np
    out_np[out_iter, :] = out_row
    
    # Increase actiheart and output iterators
    heart_iter += 1
    out_iter += 1


# In[15]:


# Get names for columns of out_np
new_cols = []
# This adds all of the column names to new_cols
new_cols.extend(actiheart_data.columns)
new_cols.extend(actigraph_data.columns)
new_cols.extend(garmin_data.columns)
new_cols.extend(apple_data.columns)
new_cols.extend(k5_data.columns)
# This labels the columns by which device the column came from
for i in range(len(new_cols)) :
    if i <= heart_cols - 1 :
        new_cols[i] = "Actiheart " + new_cols[i]
    elif i <= heart_cols + graph_cols - 1:
        new_cols[i] = "Actigraph " + new_cols[i]
    elif i <= heart_cols + graph_cols + garmin_cols - 1 :
        new_cols[i] = "Garmin " + new_cols[i]
    elif i <= heart_cols + graph_cols + garmin_cols + apple_cols - 1:
        new_cols[i] = "Apple " + new_cols[i]
    else :
        new_cols[i] = "K5 " + new_cols[i]


# In[16]:


out_df = pd.DataFrame(out_np, columns=new_cols)
out_df = out_df.iloc[:out_iter, :]
out_df


# In[39]:


out_df.columns


# In[40]:


# Remove microsecond from timestamps
def micro_remove(aTime) :
    if not pd.isnull(aTime) :
        aTime = aTime.replace(microsecond=0)
    return aTime
out_df['Actiheart ECG Time'] = out_df['Actiheart ECG Time'].apply(lambda x: micro_remove(x))
out_df['Actigraph Timestamp'] = out_df['Actigraph Timestamp'].apply(lambda x: micro_remove(x))
out_df['Apple Time'] = out_df['Apple Time'].apply(lambda x: micro_remove(x))

out_df


# In[42]:


activity = out_df['K5 Activity']
out_df.drop(columns='K5 Activity', inplace=True)
out_df.insert(0,'Activity',activity)
out_df


# In[44]:


# Function that replaces nan activities with label
label = "Break"
def label_swap(aLabel) :
    global label
    if pd.isnull(aLabel) :
        aLabel = label
    else :
        label = aLabel
    return label
out_df['Activity'] = out_df['Activity'].apply(lambda x : label_swap(x))
out_df


# In[45]:


out_df.to_csv(participant_path + "/1991_aligned.csv", index=False)


# In[ ]:




