"""
This code was written by Nicholas Tindall, research associate at the University of South Carolina, for the use of
the ACOI wearables study.
When this script is run it will read in all of the wearable device data from the PA Protocol, timestamp it, and
align it.
"""
import tkinter as tk
from tkinter import filedialog
import os
import glob
from datetime import datetime
import pandas as pd
import math
from processing_scripts.apple_processer import process_apple
from processing_scripts.garmin_processer import fit_to_csv, process_garmin
from processing_scripts.actiheart_processer import data_split, process_actiheart
from processing_scripts.k5_processer import process_k5
from processing_scripts.pa_aligner import align
from processing_scripts.data_summary import summarize, plot_hr, plot_accel, calc_enmo
from processing_scripts.aggregate import agg_to_sec
from processing_scripts.fitbit_processer import process_fitbit


def process_participant(pa_path, v_drive):
    # This line gets the path of the directory
    particpant_num = pa_path[-4:]
    print(f'Participant Number {particpant_num}')
    tracking_sheet = pd.read_excel(v_drive + "PA master tracking.xlsx")
    participant_age = tracking_sheet.loc[tracking_sheet["WDID"] == float(particpant_num), "AGE AT ENROLLMENT"]
    participant_age = math.floor(participant_age.iloc[0])
    # Initialize a list of the wearables as an empty list
    devices = []
    # Now that the path of the director I need to read in and process the following devices:

    """
    K5 PROCESSING
    The K5 can output multiple files all formatted the same way.
    For the K5 processing the files must be:
    1. Read in
    2. Timestamped
    3. Labeled by activity (Activity labels come from a separate file)
    """

    k5_path = pa_path + "/K5 data"
    activity_path = pa_path + "/Survey and Protocol documents"
    if os.path.isdir(k5_path) and os.path.isdir(activity_path):
        k5_files = glob.glob(k5_path + "/*_K5*")
        log_file = glob.glob(activity_path + "/*log*")
        # print(f"K5 files {k5_files} \nActivity Log file {log_file}")
        # Process k5 data
        print("BEGIN K5 PROCESSING")
        k5_data, activities, flags = process_k5(k5_files, log_file, k5_path, particpant_num)
        print("FINISHED")

    # Grab start and end time of trial
    trial_start = activities['1'][1]
    trial_end = activities[str(len(activities))][2]
    print(f"Trial Start: {trial_start} \nTrial End: {trial_end}")

    # APPLE WATCH Processing
    # First get the path of the Apple Watch Data files
    apple_path = pa_path + '/Apple Data'
    apple_data = pd.DataFrame()
    # Apple Watch has 2 types of data output files: Accelerometer and Heart rate. Need to grab both
    if os.path.isdir(apple_path):
        # Get list of acceleration files
        accel_files = glob.glob(apple_path + '/*_sl*.csv')
        # print(f"Apple Sensor log Files :\n{accel_files}")
        # Get list of heart rate files
        hr_files = glob.glob(apple_path + '/*_hr*.csv')
        # print(f"Cardiogram Files :\n{hr_files}")
        # Check to make sure the raw data files exist
        if len(accel_files) != 0 and len(hr_files) != 0:
            print("Begin Apple Watch Processing")
            apple_data = process_apple(accel_files, hr_files, apple_path, particpant_num, participant_age)
            devices.append("Apple")
            print("Writing Apple Summary")
            output_path = apple_path + "/Processed Data/" + particpant_num
            summarize(2, output_path, apple_data, trial_start, trial_end)
            print("Finished")


    """
    GARMIN PROCESSING
    The garmin devices output a fit file. The processing of the garmin device involves 3 steps:
    1. Convert fit file to a csv
    2. Convert garmin timestamps to time
    3. Unpack garmin acceleration data into 1 reading a row
    """

    # First get the path of the Garmin data folder
    garmin_path = pa_path + '\\Garmin data'
    # Initialize Dataframe:
    garmin_data = pd.DataFrame()
    if os.path.isdir(garmin_path):
        # Get path of all fit files
        fit_files = glob.glob(garmin_path + '/*.fit')
        # Checks that there are fit files
        if len(fit_files) != 0:
            # print(f"Fit Files: \n{fit_files}")
            # Convert fit files to csv
            fit_to_csv(fit_files, garmin_path, particpant_num)
            # Get paths of csv
            csv_files = glob.glob(garmin_path + '/*data.csv')
            # print(f"CSVs: \n{csv_files}")
            print("BEGIN GARMIN PROCESSING")
            garmin_data = process_garmin(csv_files, garmin_path, particpant_num, participant_age)
            devices.append("Garmin")
            print("Writing Garmin Summary")
            output_path = garmin_path + "/Processed Data/" + particpant_num
            summarize(3, output_path, garmin_data, trial_start, trial_end)
            print("FINISHED")

    """
    FITBIT PROCESSING
    The fitbit data comes in 2 files: acceleration and heart rate. The purpose of the processing is to read in both files,
    and combine them into one file.
    """
    # First get the path to the Fitbit Folder
    fitbit_path = pa_path + "\\Fitbit data\\"
    # Initialize Dataframe
    fitbit_data = pd.DataFrame()
    if os.path.isdir(fitbit_path) :
        # Grab accelerometer files
        fitbit_accel = glob.glob(fitbit_path + "*_accel.csv")
        # Grab Heart Rate files
        fitbit_hr = glob.glob(fitbit_path + "*_heart.csv")
        # Check if there is both an accel and HR file to merge
        if len(fitbit_accel) != 0 and len(fitbit_hr) != 0 :
            print("Begin Fitbit Processing")
            fitbit_data = process_fitbit(fitbit_accel[0], fitbit_hr[0], fitbit_path, particpant_num, participant_age)
            devices.append("Fitbit")
            print("Finished")



    """
    ACTIHEART PROCESSING
    The actiheart device outputs 2 files of interest. One file contains the heart rate and rotation for every second. The other
    file contains raw ecg and accelerometer data. The processing of the file is broken into 3 steps:
    1. Split the ecg and accelerometer data
    2. Timestamp all of the data
    3. Align the data
    """

    actiheart_path = pa_path + "/ActiHeart data"
    if os.path.isdir(actiheart_path):
        # Get the path to the ECG and Accelerometer data
        ecg_accel = glob.glob(actiheart_path + "/*combined*")
        # print(ecg_accel)
        # print(f"Raw ECG and Acceleration path: {ecg_accel}")
        # Split the ecg and acceleration files. Also grab start time of actiheart data collection
        start = data_split(ecg_accel, actiheart_path, particpant_num)
        # Get the path to the ECG data
        ecg_data = glob.glob(actiheart_path + "/*ecg_split*")
        # Get the path to the acceleration data
        accel_data = glob.glob(actiheart_path + "/*accel_split*")
        # Grab the heart rate and rotation data
        hr_data = glob.glob(actiheart_path + "/*hr*.txt")
        # print(f"ecg path {ecg_data} \naccel path {accel_data} \nheart rate path {hr_data}")
        # For a few experiments the clock of the actihearts were off. A time shift file was created for these trials that
        # stores the shift need to align actiheart
        shifts = glob.glob(actiheart_path + "/*shift.txt")
        # Process the actiheart data
        print("BEGIN ACTIHEART PROCESSING")
        actiheart_data = process_actiheart(start, ecg_data, accel_data, hr_data, shifts, actiheart_path, particpant_num,
                                           participant_age)
        print("Writing Actiheart Summary")
        output_path = actiheart_path + "/Processed Data/" + particpant_num
        # summarize(1, output_path, actiheart_data, trial_start, trial_end)
        print("FINISHED")

    """
    ALIGNMENT
    Now that all of the data has been processed it must be aligned. There are 2 steps to aligning the data:
    1. Get path to actigraph data
    2. Pass actigraph path and the data frames to the alignment script
    """
    actigraph_path = pa_path + '/ActiGraph data/csv'
    if os.path.isdir(actigraph_path):
        actigraph_path_list = glob.glob(actigraph_path + "/*acti.csv")
        # Read in actigraph data
        print("READING IN ACTIGRAPH")
        # First define a date parser. This parser allows the actigraph date format to be converted to pandas timestamp
        acti_date_parser = lambda x: datetime.strptime(x, '%m/%d/%Y %H:%M:%S.%f')
        # Read in file and store it as a dataframe.
        actigraph_data = pd.read_csv(actigraph_path_list[0], skiprows=10, parse_dates=['Timestamp'],
                                     date_parser=acti_date_parser)
        sec_frac = actigraph_data["Timestamp"].apply(lambda x: x.microsecond)
        actigraph_data.insert(1, 'Second Fraction', sec_frac)
        actigraph_data = actigraph_data.rename(
            columns={"Timestamp": "Time", "Accelerometer X": "X", "Accelerometer Y": "Y", "Accelerometer Z": "Z"})
        # print(actigraph_data)
        mag, enmo = calc_enmo(actigraph_data.loc[:, ['X', 'Y', 'Z']])
        actigraph_data.insert(5, "Magnitude", mag)
        actigraph_data.insert(6, "ENMO", enmo)

        print("Writing Actigraph Summary")
        output_path = actigraph_path[:-4] + "/Processed Data/" + particpant_num
        if os.path.isdir(output_path[:-5]) is False:
            os.mkdir(output_path[:-5])
        summarize(0, output_path, actigraph_data, trial_start, trial_end)
    else:
        actigraph_data = pd.DataFrame()
        #print(actigraph_data)

    # Align Data
    print("BEGIN ALIGNMENT")
    label = "Break"
    aligned_df = align(actigraph_data, garmin_data, apple_data, fitbit_data, actiheart_data, k5_data, pa_path, particpant_num,
                       activities, flags)
    print("BEGIN SECOND AGGREGATION")
    agg_df = agg_to_sec(aligned_df, ["Actigraph"] + devices, particpant_num, pa_path)
    print("Plotting HR")
    k5_path = k5_path + '/Processed Data/' + particpant_num + "_v02.png"
    hr_path = pa_path + "/" + particpant_num
    plot_hr(aligned_df, ["Actiheart"] + devices, trial_start, trial_end, activities, hr_path, k5_path)
    print("Plotting Accelerometers")
    #print(actigraph_data)
    if actigraph_data.shape[0] == 0:
        plot_accel(agg_df, devices, trial_start, trial_end, activities, pa_path + "/" + particpant_num)
    else :
        plot_accel(agg_df, ["Actigraph"] + devices, trial_start, trial_end, activities, pa_path + "/" + particpant_num)

    print("Finished")


if __name__ == '__main__':
    # This is used to initialize the tkinter interface where the user selects the PA Participant Folder
    root = tk.Tk()
    root.winfo_toplevel().title("Select csv files")
    root.withdraw()
    print("Select Participant to Process")
    participant = filedialog.askdirectory()  # Opens file system, prompting the user to select a folder
    parent_dir = "V:\\R01 - W4K\\3_PA protocol\\"
    if not os.path.isdir(parent_dir) :
        parent_dir = "V:\\ACOI\\R01 - W4K\\3_PA protocol\\"
    process_participant(participant, parent_dir)