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
import pandas as pd
from datetime import datetime
from processing_scripts.Apple_Proccesor import apple_process
from processing_scripts.Garmin_Processor import garmin_process
from processing_scripts.Actigraph_Processor import actigraph_process
from processing_scripts.Data_Plot import plot_accel


def process_participant(file_path):
    # ---------------------------------------------------------------------------------------------------------------------
    # This first section of code prompts the user to select the participant folder. This folder will house all of the raw
    # data from the sleep study.

    participant_path = file_path

    # Determine the Participant Number
    participant_num = participant_path[-10:]
    # print(f"Processing Participant Number: \n{participant_num}")
    # A TEst
    # ----------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------
    # Now that the path to the participant folder is known the contents of the folder need to be checked.
    # There are 5 different device data that could be stored in the folder. (Apple Watch, Garmin, Fitbit, PSG, Actigraph)
    # I will check if a folder exists for each device. If a folder does exist I will then get the file paths to the
    # raw data.

    # CHECK IF THERE IS APPLE DATA
    # The condition of this if statement is true if their is a folder named Apple Watch in the particpant's folder.
    # The condition of this if statement is true if their is a folder named Apple Watch in the particpant's folder.

    apple_path = participant_path + "\\Apple Watch"
    sensor_log = []
    auto_health = []
    if os.path.isdir(apple_path):
        sensor_log = glob.glob(apple_path + "/*_sl_*")
        # print(f"Sensor Log Files: \n{sensor_log}")
        auto_health = glob.glob(apple_path + "/*_hr.*")
        # print(f"Auto Health Files: \n{auto_health}")
        if len(sensor_log) != 0 or len(auto_health) != 0:
            apple_process(participant_num, apple_path, sensor_log, auto_health)

    # CHECK IF THERE IS GARMIN DATA
    garmin_path = participant_path + "\\Garmin"
    fit_file = []
    if os.path.isdir(garmin_path):
        fit_file = glob.glob(garmin_path + "/*.fit")
        # print(f"Fit Files: \n{fit_file}")

        i = 0
        for path in fit_file:
            # Run the jar file to convert a fit file to a csv
            jar_path = 'FitCSVTool.jar'
            # jar_path = 'V:/"ACOI"/"R01 - W4K"/"2_Shaker project"/FitSDK/java/FitCSVTool.jar'
            garmin_csv = garmin_path + "\\" + participant_num + "_Garmin_" + str(i) + ".csv"
            subprocess.call(['java', '-jar', jar_path, '-b', path, garmin_csv, '--data', 'record'])
            i += 1

        # Get the path of the data csv
        garmin_data = glob.glob(garmin_path + "\\*Garmin*data.csv")
        # print(f"Garmin Data CSV: \n{garmin_data}")
        if len(garmin_data) != 0:
            garmin_process(participant_num, garmin_path, garmin_data)

    # CHECK IF THERE IS FITBIT DATA
    fitbit_path = participant_path + "\\FitBit"
    fitbit_file = []
    if os.path.isdir(fitbit_path):
        NotImplemented

    # CHECK IF THERE IS ACTIGRAPH DATA:
    acti_path = participant_path + "\\ActiGraph\\"
    acti_file = []
    if os.path.isdir(acti_path):
        acti_data_path = acti_path + "csv"
        acti_file = glob.glob(acti_data_path + "\\*_acti.csv")
        # print(f"Actigraph File Path: {acti_file}")
        if len(acti_file) != 0:
            actigraph_process(participant_num, acti_data_path, acti_file, acti_path)

    print("Plotting All Devices")
    # Read in Apple, Actigraph, and Garmin data and then plot data.
    apple = pd.read_csv(apple_path + "/Processed Data/" + participant_num + "_apple_data.csv", parse_dates=["Time"],
                        infer_datetime_format=True)
    garmin = pd.read_csv(garmin_path + "/Processed Data/" + participant_num + "_garmin_data.csv", parse_dates=["Time"],
                         infer_datetime_format=True)
    # Read in file and store it as a dataframe.
    actigraph = pd.read_csv(acti_file[0], skiprows=10, parse_dates=['Timestamp'], date_parser=lambda x: datetime.strptime(x, '%m/%d/%Y %H:%M:%S.%f'))

    # Plot acceleration data
    plot_accel(apple, garmin, actigraph, participant_num, "X", participant_path)
    plot_accel(apple, garmin, actigraph, participant_num, "Y", participant_path)
    plot_accel(apple, garmin, actigraph, participant_num, "Z", participant_path)
    # ----------------------------------------------------------------------------------------------------------------------


root = tk.Tk()
root.winfo_toplevel().title("Select csv files")
root.withdraw()

# Start of dialogue
print("Please select the folder of the participant you wish to process")
path = filedialog.askdirectory()
process_participant(path)
