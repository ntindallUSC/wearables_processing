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
import math
from datetime import datetime, timedelta
from processing_scripts.Apple_Proccesor import apple_process
from processing_scripts.Garmin_Processor import garmin_process
from Data_Aligner import data_alignment
from Align_PSG import align_psg
from processing_scripts.agg_data import calc_enmo, agg_to_sec
from processing_scripts.Data_Plot import plot_accel, plot_hr
from processing_scripts.PSG_Processor import psg_process
from processing_scripts.Kubios_Processor import read_kubios


def process_participant(file_path, v_drive):
    # ---------------------------------------------------------------------------------------------------------------------
    # This first section of code prompts the user to select the participant folder. This folder will house all of the raw
    # data from the sleep study.

    participant_path = file_path
    devices = []
    # Determine the Participant Number
    participant_num = participant_path[-10:]
    tracking = pd.read_excel(v_drive + "\\Sleep study tracking.xlsx")
    participant_age = tracking.loc[tracking["Child ID"] == float(participant_num), "age at enrollment"]
    participant_age = math.floor(participant_age.iloc[0])
    participant_age = 8

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
            apple_data = apple_process(participant_num, apple_path, sensor_log, auto_health, participant_age)
            devices.append("Apple")
        else:
            apple_data = pd.DataFrame()
    else:
        apple_data = pd.DataFrame()

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
            garmin_data = garmin_process(participant_num, garmin_path, garmin_data, participant_age)
            devices.append("Garmin")
        else :
            garmin_data = pd.DataFrame()
    else:
        garmin_data = pd.DataFrame()

    # CHECK IF THERE IS FITBIT DATA
    fitbit_path = participant_path + "\\FitBit"
    fitbit_file = []
    if os.path.isdir(fitbit_path):
        NotImplemented

    # CHECK IF THERE IS ACTIGRAPH DATA:
    acti_path = participant_path + "\\ActiGraph\\"
    acti_file = []
    if os.path.isdir(acti_path):
        print("BEGIN ACTIGRAPH")
        acti_data_path = acti_path + "csv"
        acti_file = glob.glob(acti_data_path + "\\*_acti.csv")
        # print(f"Actigraph File Path: {acti_file}")
        actigraph = pd.read_csv(acti_file[0], skiprows=10, parse_dates=['Timestamp'],
                                date_parser=lambda x: datetime.strptime(x, '%m/%d/%Y %H:%M:%S.%f'))
        actigraph.rename(columns={"Timestamp": "Time", "Accelerometer X": "X", "Accelerometer Y": "Y",
                                  "Accelerometer Z": "Z"}, inplace=True)
        devices.insert(0, "Actigraph")
        actigraph[['X', 'Y', 'Z']] = actigraph[['X', 'Y', 'Z']].apply(pd.to_numeric)
        mag, enmo = calc_enmo(actigraph.loc[:, ["X", "Y", "Z"]])
        actigraph.insert(4, "Magnitude", mag)
        actigraph.insert(5, "ENMO", enmo)

    print("BEGIN ALIGNMENT")
    aligned_data = data_alignment(actigraph, apple_data, garmin_data, file_path, participant_num)
    print("BEGIN SECOND AGGREGATION")
    agg_data = agg_to_sec(aligned_data, participant_num, file_path, devices)
    plot_accel(agg_data, participant_num, devices, file_path + "/")

    # Check if the PSG Data exists: If it does process it:
    psg_path = participant_path + "/PSG/"
    if os.path.exists(psg_path + participant_num + "_psg.txt"):
        print("Process PSG")
        # PSG data exists, Process it
        psg_summary = psg_path + participant_num + "_psg.txt"
        psg_data = psg_path + participant_num + "_ebe.txt"
        psg_data = psg_process(participant_num, psg_path, psg_summary, psg_data)
        # Now align PSG Data with all other data
        print("Align PSG")
        align_psg(aligned_data, psg_data, participant_num, participant_path + "/")
        print("Align PSG with Aggregated Data")
        agg_data = agg_data.loc[(agg_data[agg_data.columns[0]] >= psg_data.iloc[0, 0] - timedelta(seconds=30)) &
                       (agg_data[agg_data.columns[0]] <= psg_data.iloc[-1, 0] + timedelta(seconds=30)),:]
        agg_psg = agg_data.merge(psg_data, how='left', on='Time')

        kubios_path = psg_path + "/Kubios Output/"
        if os.path.exists(kubios_path + participant_num + "_medium_hrv.csv"):
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
            if "Apple Time" in agg_psg.columns :
                plot_hr(agg_psg, "Apple", participant_path, participant_num)
            if "Garmin Time" in agg_psg.columns :
                plot_hr(agg_psg, "Garmin", participant_path, participant_num)
        agg_psg.to_csv(participant_path + "/" + participant_num + "_data_agg.csv", index=False)


    # ------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    root.winfo_toplevel().title("Select csv files")
    root.withdraw()

    # Start of dialogue
    print("Please select the folder of the participant you wish to process")
    path = filedialog.askdirectory()
    parent_dir = "V:\\R01 - W4K\\1_Sleep Study\\"
    if not os.path.isdir(parent_dir):
        parent_dir = "V:\\ACOI\\R01 - W4K\\1_Sleep Study\\"
    process_participant(path, parent_dir)
