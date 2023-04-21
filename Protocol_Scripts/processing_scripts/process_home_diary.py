#!/usr/bin/env python
# coding: utf-8

# In[2]:


import pandas as pd
from datetime import datetime, timedelta, time
import numpy as np


# In[3]:


"""
This function extracts device specific columns from the daily diary dataframe
Input:
    data   : A dataframe containg the whole daily diary
    
    device : A keyword that is used to find all columns to a specific device
    
Output:
    data[data_cols] : a dataframe containg all columns related to a specific device
"""
def extract_wearable_columns(data, device):
    data_cols = [x for x in data.columns if device in x]
    return data[data_cols]


# In[18]:


"""
This function extracts the times the device was off. The times in the following format:
'12:30 PM to 1:00 PM,1:00 PM to 1:30 PM,...' its all one string so first 
the string is split by , to get each range start and stop. Then the string is 
split by to to get each individual start and stop time
Input:
    data     : a dataframe containing all data related to a certain wearable
Output:
    time_off : a dataframe containing the time ranges that the wearable was
               not worn.
"""
def extract_time_off(data):
    # Intialize a list to hold times that a device was turned off
    time_off = []
    time_format = '%I:%M %p' # The format the off times are given in
    # First check if they wore the watch all night
    # data.iloc[1,0] corresponds to a question asking if the watch was worn
    # all night. If it's value is no then there are times to be split
    if data.iloc[1,0].lower() == 'no': 
        # Select the columns that contain wear times
        data = data.iloc[1, [4, 6, 8]].dropna()
        for value in data:
            # Split each string into on off time pairs
            for times in value.split(','):
                # Split each pair into on and off times
                time_pair = times.split('to')
                # Convert each time to a datetime and append it to a time_off
                time_off.append([datetime.strptime(time_pair[0].strip(), time_format), datetime.strptime(time_pair[1].strip(), time_format)])
    # Convert time_off to a DataFrame. It's ok if it's empty.
    # This just means that the device was worn all night.
    time_off = pd.DataFrame(time_off, columns=['Start', 'End'])
    return time_off
                
        


# In[5]:


"""
This function is used to take the protocol_date and add it to the daily diary
time, which doesn't have a date.
Input:
    data       : A dataframe containing the wear times. (Currenlty with incorrect date)
    
    prot_date  : A date extracted from tracking sheet. Correct date of protocol.
Output:
    data  :  a Dataframe with the corrected date
"""
def add_date(data, prot_date):
    if isinstance(data, pd.DataFrame):
        data = data.applymap(lambda x: x.replace(year=prot_date.year, month=prot_date.month, day=prot_date.day) if x.hour > 9 else x.replace(year=prot_date.year, month=prot_date.month, day=prot_date.day+1))
    else:
        data = data.apply(lambda x: x.replace(year=prot_date.year, month=prot_date.month, day=prot_date.day) if x.hour > 9 else x.replace(year=prot_date.year, month=prot_date.month, day=prot_date.day+1))
    return data


# In[6]:


"""
This function is used to extract all columns for a specific device from a daily diary.
This function then extracts all the wear time information from the diary and converts
them from strings to datetimes
Input:
    data   : a dataframe that contains the whole diary
    
    device : A string. This string is the key word used to search columns for specific devices

    a_date : a datetime, used to store the start date of protocol

Output:
    wearable_off : A dataframe containing 2 columns [Start, End] Each row corresponds
                   to a 30 minute segment that the device was not worn.
"""
def generate_off_times(data, device, a_date):
    wearable = extract_wearable_columns(data, device)
    # Check if wearable was worn
    if not wearable.empty:
        # Extract off time
        wearable_off = extract_time_off(wearable)
        # Add date from tracking sheet to off time
        wearable_off = add_date(wearable_off, a_date)
    else :
        # Wearable wasn't used for this experiment. It's off time should be all the night long
        time_off = pd.date_range(datetime.combine(a_date.date(), time(hour=19)), datetime.combine((a_date + timedelta(hours=24)).date(), time(hour=10)), freq='30T')
        wearable_off = pd.DataFrame(None, columns=['Start', 'End'])
        wearable_off.Start = time_off
        wearable_off.End = wearable_off['Start'].apply(lambda x: x + timedelta(minutes=30))
    return wearable_off


# In[7]:


"""
This function extracts the time a wearable device was placed on a participant
from the daily diary
Input:
    data    : a Dataframe holding all information from the daily diary
    
    a_date  : a date supplied from the master tracking sheet 
Output:
    on_time : a datetime corresponding to when the device was placed on the 
              participant.

"""

def extract_on_time(data, a_date):
    # Extract the time from the dataframe
    on_time = data[[x for x in data.columns if "put the watches on " in x]].iat[1,0]
    # Convert the time to a datetime
    on_time = a_date.replace(hour=int(on_time[:2]), minute=int(on_time[3:]))
    # Since the time was originally dateless, its possible that the device was
    # put on the following day. Check if this is the case. Increment day if needed.
    if on_time.hour <= 9:
        on_time = on_time + timedelta(hours=24)
    return on_time


# In[19]:


"""
This function extracts the time the participant went to sleep and awoke
Input:
    data    : a Dataframe holding all information from the daily diary
    
    a_date  : a date supplied from the master tracking sheet 
Output:
    on_time : a Dataframe containing the start and end of bedtime.

"""
def extract_bed_time(data, a_date):
    time_format = '%I:%M %p' # The format the off times are given in
    bed_times = data[[x for x in data.columns if "bed " in x]].iloc[1,:]
    bed_times = bed_times.apply(lambda x: datetime.strptime(x, time_format))
    bed_times = add_date(bed_times, a_date)
    bed_times = pd.DataFrame([[bed_times.iloc[0], bed_times[1]]], columns=['Start', 'End'])
    return bed_times


# In[32]:


"""
A function that generates a dataframe where each row corrsponds to a 30 minute segment
and each column corresponds to if a device was worn for that segment.
Input:
    a_date  : A date supplied from the master tracking sheet. Is used to supply the time range
              with a date.
Output:
    time_df  : a df of all 0s that has a row for each 30 minute segment from 7pm the day of the protocol
               to 10 am the day after. The dataframe has 6 rows 5 corresponding to a werable device and 
               the sixth corresponding to if the participant was in the bed.
"""
def generate_wearsheet(a_date):
    # Initialize start and end of timerange child would wear device
    time_range = (datetime.combine(a_date.date(), time(hour=19)), datetime.combine((a_date + timedelta(hours=24)).date(), time(hour=10)))
    # Create range of time with 30 Minute intervals
    time_index = pd.date_range(time_range[0], time_range[1], freq='30T')
    # Generate an array of 0s with each row corresponding to a 30 minute time interval and each column corresponding to a 
    # possible device
    time_np = np.ones([time_index.shape[0], 6])
    # Merge time index and zeros array into a dataframe
    time_df = pd.DataFrame(time_np, columns=['Actigraph On', 'Actiheart On', 'Apple On', 'Fitbit On', 'Garmin On', 'In Bed'], index=time_index)
    return time_df
    


# In[20]:


"""
A function that populates the generated wear sheet with 0s that correspond to when a
specific device was not worn
Input:
    sheet         : Dataframe generated from generate_wearsheet
    device_times  : Times that a specific device wasn't worn
    wear_start    : Time that the device was put on the participant
    device        : A string corresponding to a column header in sheet.
Output:
"""
def populate_wearsheet(sheet, device_times, wear_start, device):
    if 'In Bed' not in device:
        sheet.loc[sheet.index.intersection(device_times.Start), device] = 0
        sheet.loc[sheet.index < wear_start, device] = 0
        # If the participant wasn't wearing the device at 8:30, all times after 8:30 are marked as not worn
        if device_times.shape[0] > 0 and device_times.iloc[-1,0].time() == time(hour=8,minute=30):
            sheet.loc[sheet.index > datetime.combine(sheet.index[-1].date(), device_times.iloc[-1, 0].time()), device] = 0
    else:
        sheet.loc[(sheet.index < device_times.iat[0,0]) | (sheet.index > device_times.iat[0,1]), device] = 0
    return sheet


# In[47]:

def extract_extra_notes(data, log):
    col_name = "Is there anything else you would like to share with us about last night? - Yes, please share. - Text"
    notes = data[col_name].dropna()
    if notes.shape[0] > 1:
        log.insert(6, "Notes", "")
        log.iloc[0, 6] = notes.iloc[1]
    return log


def process_daily_diary(in_path, a_date, out_path):
    data = pd.read_csv(in_path, skiprows=1)
    # Extract each device off times:
    actigraph = generate_off_times(data, 'USC activity', a_date)
    actiheart = generate_off_times(data, 'heart rate', a_date)
    apple = generate_off_times(data, 'Apple', a_date)
    fitbit = generate_off_times(data, 'Fitbit', a_date)
    garmin = generate_off_times(data, 'Garmin', a_date)
    # Extract time the devices were put on the participant and bedtimes
    wear_start = extract_on_time(data, a_date)
    bed_times = extract_bed_time(data, a_date)
    # Generate wear sheet
    wear_sheet = generate_wearsheet(a_date)
    # Add each device's off time to sheet
    wear_sheet = populate_wearsheet(wear_sheet, actigraph, wear_start, 'Actigraph On')
    wear_sheet = populate_wearsheet(wear_sheet, actiheart, wear_start, 'Actiheart On')
    wear_sheet = populate_wearsheet(wear_sheet, apple, wear_start, 'Apple On')
    wear_sheet = populate_wearsheet(wear_sheet, fitbit, wear_start, 'Fitbit On')
    wear_sheet = populate_wearsheet(wear_sheet, garmin, wear_start, 'Garmin On')
    # Add the bedtime to the sheet
    wear_sheet = populate_wearsheet(wear_sheet, bed_times, wear_start, 'In Bed')
    # Insert notes
    wear_sheet = extract_extra_notes(data, wear_sheet)
    # Save data as a csv
    wear_sheet.to_csv(out_path)


# In[48]:


if __name__ == '__main__':
    participant_num = '0000'
    # diary_path = 'V:/ACOI/R01 - W4K/4_Free living/test data/0000/Home/Daily Diary data/0000_diary.csv'
    diary_path = 'C:/Users/Nick/Watch_Extraction/Free_Living/Test_Data/New_diary/new_diary.csv'
    # sheet_path = 'V:/ACOI/R01 - W4K/4_Free living/test data/0000/Home/Daily Diary data/' + participant_num + "_wearsheet.csv"
    sheet_path = 'C:/Users/Nick/Watch_Extraction/Free_Living/Test_Data/New_diary/test.csv'
    start_date = datetime(year=2023, month=4, day=21) # Will pull from tracking sheet in code
    process_daily_diary(diary_path, start_date, sheet_path)

