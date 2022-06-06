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






