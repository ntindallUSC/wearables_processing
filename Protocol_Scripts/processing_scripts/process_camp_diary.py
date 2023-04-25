#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
from datetime import datetime
from .k5_processer import process_labels


# In[13]:


"""
This function extracts activity specific columns from the observation diary
Input:
    data           : A dataframe containing the all columns of the observation diary
    category       : A string corresponding to on of the six possible activity categories
    column_header  : A string containing a key phrase that relates an activity category to columns in the dataframe
Output:
    categ_data     : A dataframe containing all all columns to a specific activity category
"""
def extract_activity(data, category, column_header, log_path=None):
    shared_cols = ['ID', 'Initials', 'act_start', 'act_end', 'Location','Location_13_TEXT', 'activity category']
    categ_cols = [x for x in data.columns if column_header in x]
    categ_cols = shared_cols + categ_cols
    categ_data = data.loc[data['activity category'] == category, categ_cols]
    # Occasionally there the data collector will make duplicate entries for an activity. These need to be dropped.
    categ_data = categ_data.drop(categ_data.loc[categ_data.duplicated(subset=["act_start"])].index)
    return categ_data
    


# In[4]:


"""
This function adds columns to dataframes that have less than 11. This is needed in order to concat all the activty category
dataframes.
Input:
    a_list  : A list of dataframes. Each dataframe corresponds to an activity category
Output:
    a_list  : A list of dataframes where each dataframe has at least 11 columns.
"""
def add_dummy_cols(a_list):
    new_cols = ['Participant_ID', 'Participant_Initials', 'Activity_Start', 'Activity_End', 'Location', 'Location_Text', 'Activity_Category', 'Activity', 'Activity_Text', 'Activity_Notes', 'Activity_Notes_Text']
    for ob in a_list:
        i = 0
        while ob.shape[1] < 11:
            ob.insert(ob.shape[1], "temp_" + str(i), np.nan)
            i += 1
        ob.columns=new_cols
    return a_list


# In[5]:


"""
This function splits the observational diary by activity category, extracting each column specific to each category.
Input:
    data  : a dataframe containing all the data from the observational dairy output from qulatrix
Output:
    data_act  : a list of dataframes where each dataframe houses data from 1 of the 6 possible activity categories.
"""
def split_obs(data):
    data_act = []
    data_act.append(extract_activity(data, 'Physical activity', 'phys_act'))
    data_act.append(extract_activity(data, 'Transition or break', 'transition'))
    data_act.append(extract_activity(data, 'Snack/meal', 'meal_act'))
    data_act.append(extract_activity(data, 'Enrichment or academics ', 'enrichment'))
    data_act.append(extract_activity(data, 'Putting on physical activity monitors', 'activ_monitors'))
    data_act.append(extract_activity(data, 'Other', 'other activity'))
    data_act.append(extract_activity(data, 'W4Kids PA Protocol', 'pa_protocol'))
    # Ensures that each dataframe has at least 11 columns
    data_act = add_dummy_cols(data_act)
    return data_act
    

def combine_other(col1, col2):
    col3 = str(col1) + "-" + str(col2)
    if col3[-3:] == "nan":
        col3 = col3[:-4]
    return col3

def combine_phys_activity(col1, col2):
    col3 = str(col2) + "-" + str(col1)
    return col3


def normalize_cols(a_list):
    i = 0
    for df in a_list:
        if df.shape[0] > 0:
            cols_to_drop = []
            # First combine the columns that contain other with their appropriate other text
            df['Location'] = df['Location'].combine(df['Location_Text'], combine_other)
            cols_to_drop.append('Location_Text')
            # Next check if the activity category is other. If it is combine it with it's notes
            if df.iloc[0, 6].lower() == 'other':
                df['Activity_Category'] = df['Activity_Category'].combine(df['Activity'], combine_other)
                df['Activity'] = ""
            # Move the snack and meal text entry over
            if df.iloc[0, 6].lower() == 'snack/meal':
                df['Activity_Notes'] = df['Activity_Text']
                df['Activity_Text'] = np.nan
            # Combine activity with activity_text
            df['Activity'] = df['Activity'].combine(df['Activity_Text'], combine_other)
            cols_to_drop.append('Activity_Text')
            # Add staff or children led to physical activity category
            if df.iloc[0, 6].lower() == 'physical activity':
                df['Activity_Category'] = df['Activity_Category'].combine(df['Activity_Notes'], combine_phys_activity)
                df['Activity_Notes'] = df['Activity_Notes_Text']
            cols_to_drop.append('Activity_Notes_Text')
            df.drop(columns=cols_to_drop, inplace=True)
        else:
            del a_list[i]
        i += 1
    # print(a_list)
    return a_list


# In[6]:


def convert_to_datetime(a_time, a_date):
    try :
        a_datetime = datetime(year=a_date.year, month=a_date.month, day=a_date.day, hour=int(a_time.split(':')[0]), minute=int(a_time.split(':')[1]))
    except ValueError:
        a_string = str(a_date.date()) + " " + a_time
        a_datetime = datetime.strptime(a_string, "%Y-%m-%d %I:%M %p")
    return a_datetime


# In[7]:


"""
A function that combines multiple dataframes into one.
Input:
    a_list : a list containing dataframes that correspond to each possible activity category
    a_date : a date supplied from the master tracking. Times from observational don't include dates.
Output:
    ob_df : a dataframe containing all relevant activity data sorted by time.
"""
def combine_obs(a_list, a_date):
    ob_df = pd.concat(a_list)
    # Convert Activity_Start column to datetime
    ob_df['Activity_Start'] = ob_df['Activity_Start'].apply(lambda x: convert_to_datetime(str(x), a_date))
    ob_df['Activity_End'] = ob_df['Activity_End'].apply(lambda x: convert_to_datetime(str(x), a_date))
    return ob_df.sort_values('Activity_Start')


# In[20]:


"""
A function that processes the observational dairy for free living protocol
"""
def process_observations(a_inpath, a_date, a_outpath, pa_obs):
    # Read in data and extract participant id and initials
    obs_data = pd.read_csv(a_inpath)
    # Split the data by activity category and make each activity have the same amount of columns
    obs_split = split_obs(obs_data)
    # Make all of the dataframes have the same number of columns. Combine columns where needed.
    obs_split = normalize_cols(obs_split)
    # Recombine the data 
    obs_final = combine_obs(obs_split, a_date).reset_index(drop=True)
    # Check if PA was collected for participant. If it was, then insert activities into observation sheet
    if len(pa_obs) > 0:
        pa_labels = process_labels(pa_obs, a_date)
        pa_list = []
        pa_row = obs_final.loc[obs_final['Activity_Category'] == 'W4Kids PA Protocol', :]
        pa_index = obs_final.index[obs_final['Activity_Category'] == 'W4Kids PA Protocol'].tolist()[0]

        for label in pa_labels:
            temp_row = [pa_row.iat[0,0,], pa_row.iat[0,1], pa_labels[label][1], pa_labels[label][2], pa_row.iat[0, 4],
                        pa_row.iat[0,5], pa_labels[label][0], pa_row.iat[0, 7]]
            pa_list.append(temp_row)
        pa_df = pd.DataFrame(pa_list, columns=obs_final.columns)
        #print(pa_index)
        #print(obs_final.iloc[:pa_index, -3:-1])
        obs_final = pd.concat([obs_final.iloc[:pa_index, :], pa_df, obs_final.iloc[pa_index+1:, :]])
        #print(obs_final.iloc[:, -3:-1])

    # Save dataframe to a file
    obs_final.to_csv(a_outpath, index=False)
    #print(a_outpath)


# In[21]:


if __name__ == '__main__':
    # Test to make sure everything works
    in_path = "V:/R01 - W4K/4_Free living/test data/0000/Camp/Survey and Protocol documents/0000_camp.csv"
    some_date = datetime(year=2023, month=3, day=29)
    out_path = "V:/R01 - W4K/4_Free living/test data/0000/Camp/Survey and Protocol documents/0000_camp_log.csv"
    log_path = ["V:/R01 - W4K/4_Free living/test data/0000/Camp/Survey and Protocol documents/Activity time log.xlsx"]
    process_observations(in_path, some_date, out_path, log_path)

