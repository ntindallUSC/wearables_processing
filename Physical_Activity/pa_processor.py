"""
This code was written by Nicholas Tindall, research associate at the Universtiy of South Carolina, for the use of
the ACOI wearables study.
When this script is run it will read in all of the wearable device data from the PA Protocol, timestamp it, and
align it.
"""
import tkinter as tk
from tkinter import filedialog
import glob

# This is used to intialize the tkinter interface where the user selects the PA Participant Folder
root = tk.Tk()
root.winfo_toplevel().title("Select csv files")
root.withdraw()

print("PLease select the PA Participant you wish to process")
pa_path = filedialog.askdirectory() # This line gets the path of the directory

# Now that the path of the director I need to read in the data from each device and process the data.


