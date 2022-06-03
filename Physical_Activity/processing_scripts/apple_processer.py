#!/usr/bin/env python
# coding: utf-8

# # Welcome!
# To begin running the code you must click the top left portions of each block of code. When you hover over each code's top left corner a play button should appear. Clicking this will execute that block of code. Please be sure to run the code sequentially from the top of the page to the bottom of the page.
# 
# This first little bit of code imports some packages that I will be using throughout the rest of my code. 

# In[1]:


import numpy as np
from datetime import datetime, timedelta
import csv
import io, math
import pandas as pd
import tkinter as tk
from tkinter import filedialog


# ## First you need to load the data into the script
# 
# When you run the code block below a file window should open. First you need to select the Sensorlog file that you wish to process. After that select the Auto Health File you wish to process.
# 
# Note you may need to minimize the Jupyter notebook window to see the file selection screen.

# In[2]:


# This intializes the tkinter gui
root = tk.Tk()
root.winfo_toplevel().title("Select csv files")
root.withdraw()

# Ask how many sensorlog files there are.
num = int(input("How many sensor log files do you need to process? (Please enter in a number)"))
cur_file = 0
# delim is True if the document is comma separated:
delim = ','
while cur_file < num :
    print(f"Please select sensorlog file number {cur_file+1}")
    # Get the file path of the file
    file1 = filedialog.askopenfilename()
   
    # Peek at the file to see if it is comma delimited or pipe delimited
    test = open(file1, 'r')
    line = test.readline()
    for char in line :
        if char == "|" :
            delim = '|'
            break
        elif char == ';' :
            delim = ';'
            break
        elif char == "," :
            break
    test.close()
    
     # If it's the first file read in create the accel dataframe and read in the csv file
    if cur_file == 0 :
        accel = pd.read_csv(file1, delimiter=delim)
    # Read in a file and append it to the accel data frame
    else :
        temp = pd.read_csv(file1, delimiter = delim)
        accel = pd.concat([accel,temp], ignore_index=True)
    cur_file += 1
    
# I define this function to remove the timezone from the data. I need to do this because
# The heart rate data doesn't have a timezone stamp and you cannot compare
# timezone sensitive data with timezone naive data.
def accel_time_convert(aTime) :
    a = datetime.fromisoformat(aTime[:-6])
    return a
# I apply the function above to each element in the time column
accel['loggingTime(txt)'] = accel['loggingTime(txt)'].map(lambda a : accel_time_convert(a))

# Here I convert the time columns data type to a timestamp. THis allows me to add, subtract,
# and compare time.
accel['loggingTime(txt)'] = pd.to_datetime(accel['loggingTime(txt)'])

accel.drop(columns="CMSensorRecorderAccelerometerTimestamp_sinceReboot(s)", inplace=True)
accel


# In[3]:


# Read in the heart rate file
print("Please select Auto Health File")
file2 = filedialog.askopenfilename()
heart = pd.read_csv(file2)

# Here I convert the data type in time column in the heart rate data to a timestamp
heart['Date/Time'] = pd.to_datetime(heart['Date/Time'])

heart


# In[4]:


# Get the shape of the accel and heart datafame. I will use these later
a_row, a_column = accel.shape
h_row, h_column = heart.shape

# Convert the accel and heart dataframes to numpy arrays.
# It's faster to iterate through numpy arrays than pandas dataframes.
accel_np = accel.to_numpy()
heart_np = heart.to_numpy()


# ## Process the data
# In this section of code I iterate through both the heart rate files and the acceleration files and add them to my merged array. I look at 2 adjacent acceleration readings and compare the times of recording to the time of recording of a single heart rate. There are 3 cases to consider here:<br>
# <br>1. The heart rate time stamp is less than both of the acceleration time stamps.<br>
# <br>2. The heart rate time stamp is in between two inbetween or equal to the accleration time stamps.<br>
# <br>3. The heart rate time stamp is greater than both of my acceleration time stamps.<br>
# 
# <br> Case 1 only occurs when I first begin reading the iterating through the entries. If the heart rates occur before the acceration data I iterate through the array until I find a heart rate timestamp that begins after the acceleration readings.<br>
# 
# <br> Case 2 can be caused by two different scenarios. <br>The first scenario is the heart rate timestamp falls in between 2 adjacent acceleration readings. If this is the case I take the difference between the heart rate timestamp with both of the acceleration timestamps. I then put the heart rate in the row with the acceleration time stamp it is closer to. <br>The second scenario means that their is a gap in the acceleration data. If this occurs there coud potentially be mutliple heart rate readings in the gap.  I check for this by taking the difference between the two acceleration timestamps. If difference is greater than a second I assume that their is a gap. I then add each heart rate reading that occurs in the gap to  the array without any acceleration data.<br>
# 
# <br>Case 3 occurs when 2 adjacent acceleration readings occur before a heart rate reading. I handle this by adding the 1st  acceleration reading to the array and then check the next 2 adjacent readings.<br>
# 
# 
# 

# In[5]:


# Here I intialize the numpy array that will hold both heart rate and acceleration data
# I make the # of rows in this array equal to the amount of rows the sum of the acceleration data
# and heart rate data. I do this because if for some reason there isn't any overlap in time between
# The two data sets the data structure could hold all of the information.
# Intialize output
out_np = np.empty((a_row + h_row,5), dtype="object")
# Initialize output iterator
out_iter = 0

# Intiliaze Acceleration iterator
a_iter = 0

# Intitialize Heart Rate iterator
h_iter = 0
while heart_np[h_iter, 0] < accel_np[a_iter, 0] :
    h_iter += 1
    


# In[6]:


def reading_check(device_np, device_iter, device_rows, device_cols) :
    # Get out_row, and actiheart info
    global out_row
    global accel_np
    global a_iter
    
    #   Boundary Checking          Check if current device reading occurs between 2 consecutive actiheart readings
    if device_iter < device_rows and (accel_np[a_iter, 0] <= device_np[device_iter, 0] < accel_np[a_iter + 1, 0]
                                      or accel_np[a_iter, 0] > device_np[device_iter, 0]) :      
        # Check which actiheart reading is closer to the device reading:
        if abs(accel_np[a_iter, 0] - device_np[device_iter, 0]) <= abs(accel_np[a_iter + 1, 0] - device_np[device_iter, 0]):
            out_row.append(device_np[device_iter, 1])
            device_iter += 1
        else :
            out_row.append(np.nan)

    else : # No device reading occured
        out_row.append(np.nan)
    
    return device_iter


# In[7]:


# Begin alignment
while a_iter < a_row - 1 :
    # Intialize output row
    out_row = []
    
    # Checks for gaps in accelerometer
    if accel_np[a_iter + 1, 0] - accel_np[a_iter, 0] > timedelta(seconds=1) :
        print(f"Gap found between {accel_np[a_iter, 0]} and {accel_np[a_iter + 1, 0]}")
        # Add acceleration value 
        for value in accel_np[a_iter, :] :
            out_row.append(value)
        # Check if heart rate value should be added
        if accel_np[a_iter, 0] > heart_np[h_iter, 0] :
            out_row. append(heart_np[h_iter, 1])
            h_iter += 1
        else :
            out_row.append(np.nan)
        # Add reading to output and iterate
        out_np[out_iter, :] = out_row
        out_iter += 1
        a_iter += 1
        # Add heartrates that fall into the gap
        while h_iter < h_row and accel_np[a_iter, 0] > heart_np[h_iter, 0] :
            out_row = [np.nan, np.nan, np.nan, np.nan, heart_np[h_iter, 1]]
            out_np[out_iter, :] = out_row
            h_iter += 1
            out_iter += 1
        out_row = []
        
    
    for value in accel_np[a_iter, :] :
        out_row.append(value)
    
    # Check if heart rate reading is needed
    h_iter = reading_check(heart_np, h_iter, h_row, h_column)
    
    # Add to output
    # print(out_row)
    out_np[out_iter, :] = out_row[:]
    
    a_iter += 1
    out_iter += 1
out_row = []
for value in accel_np[a_iter, :] :
    out_row.append(value)
if h_iter < h_row and heart_np[h_iter, 0] <= accel_np[a_iter, 0] :
    out_row.append(heart_np[h_iter, 1])
else :
    out_row.append(np.nan)
out_np[out_iter, :] = out_row


# In[15]:


# Convert the merged numpy array to a Pandas dataframe. I do this to make it easier to output as a csv
final_df = pd.DataFrame(out_np, columns = ['Time', 'X', 'Y', 'Z', 'Heart Rate'])
final_df.drop(final_df.iloc[out_iter:].index, inplace=True)
# Get Second Fraction
sec_frac = final_df["Time"].apply(lambda x: x.microsecond)
# Insert Second Fraction into df
final_df.insert(1, "Second Fraction", sec_frac)
final_df


# # Sanity check
# The next 2 lines of code gets the number of heart rate readings in the output df and the number of heart rate readings from the orignal file that occur during the acceleration detection. These values should be the same

# In[16]:


final_df["Heart Rate"].count()


# In[17]:


heart.loc[(heart["Date/Time"] >= accel.iloc[0,0]) & (heart["Date/Time"] <= accel.iloc[-1,0]), "Min (count/min)"].count()


# ## Create new CSV File
# Running this code creates a new CSV 

# In[18]:


out_file = filedialog.askdirectory()
final_df.to_csv(out_file + "/1991_apple.csv", index=False)


# In[ ]:




