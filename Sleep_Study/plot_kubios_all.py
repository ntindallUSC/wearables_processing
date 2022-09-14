"""
The purpose of this script is to help automate the data processing of the Wearables sleep study conducted by the ACOI.
This script will prompt the user to select a participant folder, and then grab the files needed to be processed.
The script will then pass the files to the appropriate processing script which will output a csv.


This code was written by Nicholas Tindall
"""

import glob
import os.path
import pandas as pd
from processing_scripts.Data_Plot import plot_hr
from processing_scripts.Kubios_Processor import read_kubios


def process_participant(file_path):
    # ---------------------------------------------------------------------------------------------------------------------
    # This first section of code prompts the user to select the participant folder. This folder will house all of the raw
    # data from the sleep study.

    participant_path = file_path
    # Determine the Participant Number
    participant_num = participant_path[-10:]
    kubios_path = participant_path + "/PSG//Kubios Output/"
    if os.path.exists(kubios_path + participant_num + "_medium_hrv.csv"):
        print("Found Kubios Data")
        agg_psg = pd.read_csv(participant_path + "/" + participant_num + "_data_agg.csv", parse_dates=['Time'],
                              infer_datetime_format=True)
        agg_psg["Apple Time"] = agg_psg["Apple Time"].apply(lambda x: pd.to_datetime(x))
        agg_psg["Garmin Time"] = agg_psg["Garmin Time"].apply(lambda x: pd.to_datetime(x))
        # Check if the Kubios Heart rate Data exists: If it does process it:
        # Get the paths of the 2 different kubios outputs
        medium_path = kubios_path + participant_num + "_medium_hrv.csv"
        none_path = kubios_path + participant_num + "_none_hrv.csv"

        # Read in the data
        kubios_med = read_kubios(medium_path, True, participant_num)
        kubios_none = read_kubios(none_path, False, participant_num)
        # Merge two data sets
        kubios_hr = kubios_med.merge(kubios_none, how="inner", on='Time')
        agg_psg = agg_psg.merge(kubios_hr, how="left", on="Time")
        plot_hr(agg_psg, participant_path, participant_num)


    agg_psg.to_csv(participant_path + "/" + participant_num + "_data_agg.csv", index=False)


    # ------------------------------------------------------------------------------------------------------------------

# Intialize path to folder containing all the participant files
parent_dir = "V:\\R01 - W4K\\1_Sleep Study\\1_Participant Data"

# Create a list of all the participant files
participants = glob.glob(parent_dir + "\\7*")
# Process all participants
i = 1
total_participants = len(participants)

for participant in participants:
    print(f"PROCESSING {i}/{total_participants}")
    print(f"Participant {participant[-10:]}")
    # Process the Apple, Garmin, and Actigraph Data
    process_participant(participant)

    i += 1


