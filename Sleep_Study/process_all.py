"""
The purpose of this script is to help automate the data processing of the Wearables sleep study conducted by the ACOI.
This script will prompt the user to select a participant folder, and then grab the files needed to be processed.
The script will then pass the files to the appropriate processing script which will output a csv.


This code was written by Nicholas Tindall
"""

import glob
from process import process_participant
from Data_Aligner import data_alignment

# Intialize path to folcer containing all the participant files
parent_dir = "V:\\R01 - W4K\\1_Sleep Study"

# Create a list of all the participant files
participants = glob.glob(parent_dir + "\\7*")
# Process all participants
i = 15
total_participants = len(participants)
participants = participants[13:]

for participant in participants:
    print(f"PROCESSING {i}/{total_participants}")
    print(f"Participant {participant[-10:]}")
    # Process the Apple, Garmin, and Actigraph Data
    process_participant(participant)

    # Check if PSG Data exists
    psg_files = glob.glob(participant + "/PSG/*ebe*")  # Gets a list of paths of psg files
    if len(psg_files) > 0:  # If the list's length is > 0 then psg files exist and the data needs to be aligned
        print("PSG detected. Aligning Data")
        data_alignment(participant)
    else:
        print("No PSG Detected")
    i += 1
