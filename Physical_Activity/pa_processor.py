"""
This code was written by Nicholas Tindall, research associate at the Universtiy of South Carolina, for the use of
the ACOI wearables study.
When this script is run it will read in all of the wearable device data from the PA Protocol, timestamp it, and
align it.
"""
import tkinter as tk
from tkinter import filedialog
import os
import glob
from processing_scripts.apple_processer import process_apple
from processing_scripts.garmin_processer import fit_to_csv, process_garmin
from processing_scripts.actiheart_processer import data_split, process_actiheart
from processing_scripts.k5_processer import process_k5
from processing_scripts.

# This is used to intialize the tkinter interface where the user selects the PA Participant Folder
root = tk.Tk()
root.winfo_toplevel().title("Select csv files")
root.withdraw()

print("PLease select the PA Participant you wish to process")
pa_path = filedialog.askdirectory() # This line gets the path of the directory
particpant_num = pa_path[-4:]
print(f'Participant Number {particpant_num}')

# Now that the path of the director I need to read in and process the following devices:

# APPLE WATCH Processing
# First get the path of the Apple Watch Data files
"""
apple_path = pa_path + '/Apple Data'
apple_data = None
# Apple Watch has 2 types of data output files: Accelerometer and Heart rate. Need to grab both
if os.path.isdir(apple_path):
    # Get list of acceleration files
    accel_files = glob.glob(apple_path + '/*_sl*.csv')
    print(f"Apple Sensor log Files :\n{accel_files}")
    # Get list of heart rate files
    hr_files = glob.glob(apple_path + '/*_hr.csv')
    print(f"Cardiogram Files :\n{hr_files}")
    print("Begin Apple Watch Processing")
    apple_data = process_apple(accel_files, hr_files, apple_path, particpant_num)
    print("Finished")
"""

"""
GARMIN PROCESSING
The garmin devices output a fit file. The processing of the garmin device involves 3 steps:
1. Convert fit file to a csv
2. Convert garmin timestamps to time
3. Unpack garmin acceleration data into 1 reading a row
"""
"""
# First get the path of the Garmin data folder
garmin_path = pa_path + '\\Garmin data'
# Check if folder exists:
if os.path.isdir(garmin_path):
    # Get path of all fit files
    fit_files = glob.glob(garmin_path + '/*.fit')
    print(f"Fit Files: \n{fit_files}")
    # Convert fit files to csv
    fit_to_csv(fit_files, garmin_path, particpant_num)
    # Get paths of csv
    csv_files = glob.glob(garmin_path + '/*data.csv')
    print(f"CSVs: \n{csv_files}")
    garmin_data = process_garmin(csv_files, garmin_path, particpant_num)
"""


"""
ACTIHEART PROCESSING
The actiheart device outputs 2 files of interest. One file contains the heart rate and rotation for every second. The other
file contains raw ecg and accelerometer data. The processing of the file is broken into 3 steps:
1. Split the ecg and accelerometer data
2. Timestamp all of the data
3. Align the data
"""
"""
actiheart_path = pa_path + "/ActiHeart data"
if os.path.isdir(actiheart_path):
    # Get the path to the ECG and Accelerometer data
    ecg_accel = glob.glob(actiheart_path + "/*ECG_accel*")
    print(f"Raw ECG and Acceleration path: {ecg_accel}")
    # Split the ecg and acceleration files. Also grab start time of actiheart data collection
    start = data_split(ecg_accel, actiheart_path, particpant_num)
    # Get the path to the ECG data
    ecg_data = glob.glob(actiheart_path + "/*ecg_split*")
    # Get the path to the acceleration data
    accel_data = glob.glob(actiheart_path + "/*accel_split*")
    # Grab the heart rate and rotation data
    hr_data = glob.glob(actiheart_path + "/*per*sec*")
    print(f"ecg path {ecg_data} \naccel path {accel_data} \nheart rate path {hr_data}")
    # Process the actiheart data
    actiheart_data = process_actiheart(start, ecg_data, accel_data, hr_data, actiheart_path, particpant_num)
"""
"""
K5 PROCESSING
The K5 can output multiple files all formatted the same way. 
For the K5 processing the files must be:
1. Read in
2. Timestamped
3. Labeled by activity (Activity labels come from a separate file)
"""
"""
k5_path = pa_path + "/K5 data"
activity_path = pa_path + "/Survey and Protocol documents"
if os.path.isdir(k5_path) and os.path.isdir(activity_path):
    k5_files = glob.glob(k5_path + "/*_K5*")
    log_file = glob.glob(activity_path + "/*log*")
    print(f"K5 files {k5_files} \nActivity Log file {log_file[0]}")
    # Process k5 data
    k5_data = process_k5(k5_files, log_file, k5_path, particpant_num)
"""
"""
ALIGNMENT
Now that all of the data has been processed it must be aligned. There are 2 steps to aligning the data:
1. Get path to actigraph data
2. Pass actigraph path and the data frames to the alignment script
"""
actigraph_path = pa_path + '/ActiGraph data/csv'
if os.path.isdir(actigraph_path):
    actigraph_data = glob.glob(actigraph_path + "/*acti.csv")
    print(f"Actigraph Path: {actigraph_data}")

# Align Data





