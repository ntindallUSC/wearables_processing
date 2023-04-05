#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
from datetime import datetime


# In[13]:


"""
This function extracts activity specific columns from the observation diary
Input:
    data           : A dataframe containing the all columns of the observation diary
    category       : A string correspodning to on of the six possible activity categories
    column_header  : A string containing a key phrase that relates an activity category to columns in the dataframe
Output:
    categ_data     : A dataframe containing all all columns to a specific activity category
"""
def extract_activity(data, category, column_header):
    shared_cols = ['ID', 'Initials', 'act_start', 'act_end', 'Location','Location_13_TEXT', 'activity category']
    categ_cols = [x for x in data.columns if column_header in x]
    categ_cols = shared_cols + categ_cols
    categ_data = data.loc[data['activity category'] == category, categ_cols]
    # Occasionally there the data collecter will make duplicate entries for an activity. These need to be dropped.
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
    # Ensures that each dataframe has at least 11 columns
    data_act = add_dummy_cols(data_act)
    return data_act
    
    


# In[6]:


def convert_to_datetime(a_time, a_date):
    return datetime(year=a_date.year, month=a_date.month, day=a_date.day, hour=int(a_time.split(':')[0]), minute=int(a_time.split(':')[1]))


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
    ob_df['Activity_Start'] = ob_df['Activity_Start'].apply(lambda x: convert_to_datetime(x, a_date))
    ob_df['Activity_End'] = ob_df['Activity_End'].apply(lambda x: convert_to_datetime(x, a_date))
    return ob_df.sort_values('Activity_Start')


# In[20]:


"""
A function that processes the observational dairy for free living protocol
"""
def process_observations(a_inpath, a_date, a_outpath):
    # Read in data and extract participant id and initials
    obs_data = pd.read_csv(a_inpath)
    # Split the data by activity category and make each activity have the same amount of columns
    obs_split = split_obs(obs_data)
    # Recombine the data 
    obs_final = combine_obs(obs_split, a_date)
    # Save dataframe to a file
    obs_final.to_csv(a_outpath, index=False)


# In[21]:


if __name__ == '__main__':
    # Test to make sure everything works
    in_path = "V:/ACOI/R01 - W4K/4_Free living/test data/0000/Camp/Survey and Protocol documents/0000_program observation.csv"
    some_date = datetime(year=2023, month=3, day=29)
    out_path = "V:/ACOI/R01 - W4K/4_Free living/test data/0000/Camp/Survey and Protocol documents/000_activity_log.csv"
    process_observations(in_path, some_date, out_path)

