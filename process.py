"""
The purpose of this script is to help automate the data processing of the Wearables sleep study conducted by the ACOI.
This script will prompt the user to select a participant folder, and then grab the files needed to be processed.
The script will then pass the files to the appropriate processing script which will output a csv.


This code was written by Nicholas Tindall
"""

import glob
import tkinter as tk
from tkinter import filedialog
import os.path
import subprocess
from processing_scripts.Apple_Proccesor import apple_process
from processing_scripts.Garmin_Processor import garmin_process

# ---------------------------------------------------------------------------------------------------------------------
# This first section of code prompts the user to select the participant folder. This folder will house all of the raw
# data from the sleep study.

root = tk.Tk()
root.winfo_toplevel().title("Select csv files")
root.withdraw()

# Start of dialogue
print("Please select the folder of the participant you wish to process")
participant_path = filedialog.askdirectory()
print(f"Path to Participant Folder: \n{participant_path}")
# Determine the Participant Number
participant_num = participant_path[-10:]
print(f"Participant Number: \n{participant_num}")
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Now that the path to the participant folder is known the contents of the folder need to be checked.
# There are 5 different device data that could be stored in the folder. (Apple Watch, Garmin, Fitbit, PSG, Actigraph)
# I will check if a folder exists for each device. If a folder does exist I will then get the file paths to the
# raw data.


# CHECK IF THERE IS APPLE DATA
# The condition of this if statement is true if their is a folder named Apple Watch in the particpant's folder.
apple_path = participant_path + "\\Apple Watch"
sensor_log = []
auto_health = []
if os.path.isdir(apple_path):
    sensor_log = glob.glob(apple_path + "/*_sl_*")
    print(f"Sensor Log Files: \n{sensor_log}")
    auto_health = glob.glob(apple_path + "/*_hr.*")
    print(f"Auto Health Files: \n{auto_health}")

apple_process(participant_num, apple_path, sensor_log, auto_health)

# CHECK IF THERE IS GARMIN DATA

garmin_path = participant_path + "\\Garmin"
fit_file = []
if os.path.isdir(garmin_path):
    fit_file = glob.glob(garmin_path + "/*.fit")
    print(f"Fit Files: \n{fit_file}")

    i = 0
    for path in fit_file:
        # Run the jar file to convert a fit file to a csv
        jar_path = 'FitCSVTool.jar'
        # jar_path = 'V:/"ACOI"/"R01 - W4K"/"2_Shaker project"/FitSDK/java/FitCSVTool.jar'
        garmin_csv = garmin_path + "\\" + participant_num + "_Garmin_" + str(i) + ".csv"
        subprocess.call(['java', '-jar', jar_path, '-b', path, garmin_csv, '--data', 'record'])
        i += 1


    # Get the path of the data csv
    garmin_data = glob.glob(garmin_path + "\\*data.csv")
    print(f"Garmin Data CSV: \n{garmin_data}")
    garmin_process(participant_num, garmin_path, garmin_data)


# CHECK IF THERE IS FITBIT DATA
fitbit_path = participant_path + "\\FitBit"
fitbit_file = []
if os.path.isdir(fitbit_path):
    NotImplemented


# ----------------------------------------------------------------------------------------------------------------------
