"""
This script visaualizes all of the Heart Rate, V02/kg, and accelerometer data for each participant in the PA study
"""
import glob
from os.path import exists
from processing_scripts.k5_processer import process_k5
from datetime import datetime
import pandas as pd
from processing_scripts.data_summary import summarize, plot_hr, plot_accel

pa_path = 'V:/R01 - W4K/3_PA protocol/1_Participants/'
participants = glob.glob(pa_path + "[0-9][0-9][0-9][0-9]")
for participant in participants :
    participant_num = participant[-4:]
    print(f"Visualizing Participant {participant_num}")
    # intialize path to files needed for data visualization
    data_path = participant + "/" + participant_num + "_aligned.csv"
    k5_path = glob.glob(participant + "/K5 data/*_K5*")
    log_path = glob.glob(participant + "/Survey and Protocol documents/*log*")
    if exists(data_path):
        # Call this function to get a dictionary of activities performed during the protocol
        k5_data, activities = process_k5(k5_path, log_path, participant + "/K5 data", participant_num)

        # Grab start and end time of trial
        trial_start = activities['1'][1]
        trial_end = activities[str(len(activities))][2]

        # Read in trial data
        data = pd.read_csv(data_path)
        data["Actiheart ECG Time"] = pd.to_datetime(data["Actiheart ECG Time"])
        data["Actigraph Timestamp"] = pd.to_datetime(data["Actigraph Timestamp"])
        data["Garmin Time"] = pd.to_datetime(data["Garmin Time"])
        data["Apple Time"] = pd.to_datetime(data["Apple Time"])
        data["K5 t"] = pd.to_datetime(data["K5 t"])

        # Plot all the data
        plot_hr(data, trial_start, trial_end, activities, participant, participant + "/K5 Data/Processed Data/" + participant_num + "_v02.png")
        plot_accel(data, trial_start, trial_end, "X", activities, participant + "/" + participant_num)
        plot_accel(data, trial_start, trial_end, "Y", activities, participant + "/" + participant_num)
        plot_accel(data, trial_start, trial_end, "Z", activities, participant + "/" + participant_num)

    else:
        print("No data found")


print("Finished Plotting all available data")
