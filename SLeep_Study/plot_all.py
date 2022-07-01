"""
This script visaualizes all of the Heart Rateand accelerometer data for each participant in the Sleep study
"""
import glob
from datetime import datetime
import pandas as pd
from processing_scripts.Data_Plot import plot_accel
from os.path import exists

# Get all sleep participant folders
sleep_path = "V:/R01 - W4K/1_Sleep Study/1_Participant Data"
participants = glob.glob(sleep_path + "751[0-9][0-9]*")

for participant in participants:
    participant_num = participant[-10:]
    print(f"Starting {participant_num}")
    apple_path = participant + "/Apple Watch/Processed Data/" + participant_num + "_apple_data.csv"
    garmin_path = participant + "/Garmin/Processed Data/" + participant_num + "_garmin_data.csv"
    acti_path = participant + "/Actigraph/csv/" + participant_num + "_acti.csv"

    if exists(apple_path) and exists(garmin_path) and exists(acti_path):
        # Read in Apple, Actigraph, and Garmin data and then plot data.
        apple = pd.read_csv(apple_path, parse_dates=["Time"], infer_datetime_format=True)
        garmin = pd.read_csv(garmin_path, parse_dates=["Time"], infer_datetime_format=True)
        actigraph = pd.read_csv(acti_path, skiprows=10, parse_dates=['Timestamp'],
                                date_parser=lambda x: datetime.strptime(x, '%m/%d/%Y %H:%M:%S.%f'))

        print("Plotting X")
        plot_accel(apple, garmin, actigraph, participant_num, 'X', participant + "/")
        print("Plotting Y")
        plot_accel(apple, garmin, actigraph, participant_num, 'Y', participant + "/")
        print("Plotting Z")
        plot_accel(apple, garmin, actigraph, participant_num, 'Z', participant + "/")
    else:
        print("Missing Data. No plot. :(")

    print(f"Finished {participant_num}")
