import glob
import tkinter as tk
from tkinter import filedialog
import os.path
import pandas as pd
import math
from datetime import datetime, timedelta
from .processing_scripts.apple_processer import process_apple
from .processing_scripts.garmin_processer import fit_to_csv, process_garmin
from .processing_scripts.fitbit_processer import timestamp_fitbit, combine_fitbit
from .processing_scripts.actigraph_processer import process_actigraph
from .processing_scripts.PSG_Processor import psg_process
from .processing_scripts.Kubios_Processor import read_kubios
from .processing_scripts.data_summary import summarize
from .processing_scripts.merge_data import align
from .processing_scripts.aggregate import agg_to_sec
from .processing_scripts.k5_processer import process_k5, process_labels, process_flags
from .processing_scripts.actiheart_processer import process_actiheart, plot_actiheart_hr, process_actiheart_sleep
from .processing_scripts.process_camp_diary import process_observations
from .processing_scripts.process_home_diary import process_daily_diary


def process_participant(in_path, v_drive, protocol='PA'):
    # Pulls meta data from protocol tracking sheet for particular participant
    # List used to keep track of devices processed
    devices = []
    # This line gets the path of the directory
    if protocol == 'Sleep':
        participant_num = in_path[-10:]
        print(f'Sleep Participant Number {participant_num}')
        # Grab the participant age, start, and stop time of protocol from tracking sheet.
        tracking_sheet = pd.read_excel(v_drive + "Sleep study tracking.xlsx")
        participant_age = tracking_sheet.loc[tracking_sheet["Child ID"] == float(participant_num), "age at enrollment"]
        participant_age = math.floor(participant_age.iloc[0])
        devices_time = tracking_sheet.loc[
            tracking_sheet["Child ID"] == float(participant_num), ["Date of Visit", "Devices time on",
                                                                   "Devices time off"]]
        trial_start = datetime.combine(devices_time.iloc[0, 0].to_pydatetime().date(), devices_time.iloc[0, 1])
        trial_end = datetime.combine(devices_time.iloc[0, 0].to_pydatetime().date(),
                                     devices_time.iloc[0, 2]) + timedelta(
            hours=24)
        activities = None
        flags = None
    elif protocol == 'PA':
        participant_num = in_path[-4:]
        print(f'PA Participant Number {participant_num}')
        # Grab the participant age and date of protocol from tracking sheet
        tracking_sheet = pd.read_excel(v_drive + "PA master tracking.xlsx")
        participant_age = math.floor(
            tracking_sheet.loc[tracking_sheet["WDID"] == float(participant_num), "AGE AT PROTOCOL DATE"].iat[0])
        protocol_date = tracking_sheet.loc[tracking_sheet["WDID"] == float(participant_num), ["PROTOCOL DATE"]].iat[
            0, 0]
        # Grab the start and stop times of protocol from the activity log. (Combine times with date)
        activity_path = in_path + "/Survey and Protocol documents"
        log_file = glob.glob(activity_path + "/*log*")
        if len(log_file) > 0:
            activities = process_labels(log_file, protocol_date)
            flags = process_flags(log_file, protocol_date)
            # Grab start and end time of trial
            trial_start = activities['1'][1]
            trial_end = activities[str(len(activities))][2]
    elif protocol[:2] == 'FL':
        participant_num = in_path[-4:]
        print(f'Free Living Participant Number {participant_num}')
        tracking_sheet = pd.read_excel(v_drive + "Free-living master tracking.xlsx", skiprows=1)
        # Grab participant age and date of the protocol
        participant_age = math.floor(tracking_sheet.loc[tracking_sheet["WDID"] == float(participant_num), "AGE AT PROTOCOL DATE"].iat[0])

        # Define path to the observation form
        activities = None
        flags = None
        if protocol.split("-")[1] == 'camp':
            print("BEGIN CAMP DATA PROCESSING")
            protocol_date = tracking_sheet.loc[tracking_sheet["WDID"] == float(participant_num), ["PROTOCOL DATE"]].iat[
                0, 0]
            in_path += "/Camp"
            observation_path = in_path + "/Survey and Protocol documents/"
            obs_file = glob.glob(observation_path + "*camp.csv")[0]
            activ_log = glob.glob(observation_path + "Activity*time*log.xlsx")
            process_observations(obs_file, protocol_date, in_path + "/" + participant_num + "_camp_log.csv", activ_log)
            device_times = tracking_sheet.loc[tracking_sheet["WDID"] == float(participant_num), ["ALL DEVICES ON: CAMP", "ALL DEVICES OFF: CAMP"]]
            trial_start = datetime.combine(protocol_date, device_times.iat[0, 0])
            trial_end = datetime.combine(protocol_date, device_times.iat[0, 1])
        else:
            print("BEGIN AT HOME DATA PROCESSING")
            protocol_date = tracking_sheet.loc[tracking_sheet["WDID"] == float(participant_num), ["NIGHT OF SLEEP"]].iat[
                0, 0]
            in_path += "/Home"
            diary_path = in_path + "/Daily Diary data/"
            diary_file = glob.glob(diary_path + "*home.csv")[0]
            process_daily_diary(diary_file, protocol_date, in_path + "/" + participant_num + "_home_log.csv")
            device_times = tracking_sheet.loc[tracking_sheet["WDID"] == float(participant_num), ["ALL DEVICES ON: HOME", "ALL DEVICES OFF: HOME"]]
            trial_start = datetime.combine(protocol_date, device_times.iat[0, 0])
            trial_end = datetime.combine(protocol_date, device_times.iat[0, 1])
            if 0 < trial_end.hour <= 10:
                trial_end += timedelta(hours=24)
    else:
            print("NO ACTIVITY LOG FILE DETECTED. PLEASE MAKE ONE AND THEN PROCESS.")
            return 1
    print(trial_start)
    print(trial_end)

    # Process Apple Data
    if protocol == "Sleep":
        apple_path = in_path + "/Apple Watch/"
    elif protocol == "PA" or protocol[:2] == 'FL':
        apple_path = in_path + "/Apple Data/"
    # Use glob to create a list of paths of all Sensor Log files
    accel_files = glob.glob(apple_path + "*_sl*.csv")
    # accel_files = []
    # Use glob to create a list of paths of all Heart Rate files
    hr_files = glob.glob(apple_path + "*_hr*.csv")
    # If both lists aren't empty process the apple data
    if len(accel_files) > 0 and len(hr_files) > 0:
        print("Begin Apple Watch Processing")
        devices.append(
            process_apple(accel_files, hr_files, apple_path, participant_num, participant_age, trial_start, trial_end,
                          "sleep"))
        print("Writing Apple Summary")
        output_path = apple_path + "/Processed Data/" + participant_num
        summarize(2, output_path, devices[-1][1], trial_start, trial_end)
        print("Finished")

    # Process Fitbit data
    if protocol == "Sleep":
        fitbit_path = in_path + "/Fitbit/"
    elif protocol == "PA" or protocol[:2] == 'FL':
        fitbit_path = in_path + "/Fitbit data/"
    # Use glob to get list of accel and heart rate files
    fb_accel_path = glob.glob(fitbit_path + "/Batch data/Accel*.csv")
    # fb_accel_path = []
    fb_hr_path = glob.glob(fitbit_path + "/Batch data/Heart_combined*.csv")
    # If there are files process them
    # fitabase hr for comparison
    fitabase = glob.glob(fitbit_path + "/Fitabase/*_hr.csv")
    if len(fb_accel_path) > 0 and len(fb_hr_path) > 0:
        print("Begin Fitbit Processing")
        # Check if the correct timestamp files already exist
        if not os.path.exists(fitbit_path + participant_num + "_heart.csv"):
            fitbit_accel, fitbit_hr = timestamp_fitbit(fb_accel_path, fb_hr_path, fitbit_path, participant_num)
            # fitbit_accel, fitbit_hr = timestamp_fitbit(fb_accel_path[0], fb_hr_path[0], fitbit_path, participant_num)
        else:
            # The files have been timestamped. Just read them in and combine them
            fitbit_accel = pd.read_csv(fitbit_path + participant_num + "_accel.csv", parse_dates=['Time'],
                                       infer_datetime_format=True)
            fitbit_hr = pd.read_csv(fitbit_path + participant_num + "_heart.csv", parse_dates=['Time'],
                                    infer_datetime_format=True)
        devices.append(
            combine_fitbit(fitbit_accel, fitbit_hr, fitbit_path, participant_num, participant_age, trial_start,
                           trial_end, "sleep"))
        print("Writing Fitbit Summary")
        output_path = fitbit_path + "/Processed Data/" + participant_num
        summarize(4, output_path, devices[-1][1], trial_start, trial_end, fitabase)
        print("FINISHED")

    # Process Garmin Data
    if protocol == "Sleep":
        garmin_path = in_path + "/Garmin/"
    elif protocol == "PA" or protocol[:2] == 'FL':
        garmin_path = in_path + "/Garmin data/"
    # First use glob to create a list of all garmin fit files
    fit_files = glob.glob(garmin_path + "*.fit")
    # fit_files = []
    # If there are files then begin processing
    if len(fit_files) > 0:
        print("Begin Garmin Processing")
        # Check to see if the FIT Files have already been converted to csv
        csv_files = glob.glob(garmin_path + "*data.csv")
        if len(csv_files) == 0:
            print("No csv files detected. Converting fit to csv")
            # Convert FIT files to csv using function provided by Garmin
            fit_to_csv(fit_files, garmin_path, participant_num)
            # Create list of paths of CSV files
            csv_files = glob.glob(garmin_path + "*data.csv")
        devices.append(
            process_garmin(csv_files, garmin_path, participant_num, participant_age, trial_start, trial_end, "sleep"))
        print("Writing Garmin Summary")
        output_path = garmin_path + "/Processed Data/" + participant_num
        summarize(3, output_path, devices[-1][1], trial_start, trial_end)
        print("FINISHED")

    # Process Actigraph
    if protocol == "Sleep":
        actigraph_path = in_path + "/ActiGraph/csv/"
    elif protocol == "PA" or protocol[:2] == 'FL':
        actigraph_path = in_path + "/ActiGraph data/csv/"
    # Get list of paths to actigraph
    acti_files = glob.glob(actigraph_path + "*acti.csv")
    # acti_files = []
    if len(acti_files) > 0:
        print("Processing Actigraph")
        devices.insert(0, (process_actigraph(acti_files, trial_start, trial_end)))
        print("Writing Actigraph Summary")
        output_path = actigraph_path[:-5] + "/Processed Data/" + participant_num
        if os.path.isdir(output_path[:-1 * (len(participant_num) + 1)]) is False:
            os.mkdir(output_path[:-1 * (len(participant_num) + 1)])
        elif protocol == "PA":
            if os.path.isdir(output_path[:-5]) is False:
                os.mkdir(output_path[:-5])
        summarize(0, output_path, devices[0][1], trial_start, trial_end)
        print("Finished")

    # Process Actiheart
    actiheart_path = in_path + "/ActiHeart data/"
    actiheart_files = glob.glob(actiheart_path + "*_hr*.txt")

    if len(actiheart_files) > 0:
        print("Processing Actiheart")
        # For a few of the experients the actiheart clock was off for these experiements a shift file was made
        # to be used to align the data
        shift_files = glob.glob(actiheart_path + "*shift.txt")
        devices.append(process_actiheart(actiheart_files, shift_files, actiheart_path, participant_num, participant_age,
                                         trial_start, trial_end, protocol))
        if protocol[:2] == "FL":
            plot_actiheart_hr(devices[-1][1], actiheart_path + "/Processed Data/" + participant_num + "_" + protocol.split("-")[1] + '_hr.png')
        else:
            plot_actiheart_hr(devices[-1][1],
                              actiheart_path + "/Processed Data/" + participant_num + '_hr.png')

    # Process the PSG Files
    psg_path = in_path + "/PSG/"
    # Collect the path to the PSG Summary and Data
    psg_summary = glob.glob(psg_path + "*_psg.txt")
    psg_labels = glob.glob(psg_path + "*_ebe.txt")
    # psg_labels = []
    if len(psg_summary) > 0 and len(psg_labels) > 0:
        print("Begin PSG Processing")
        devices.append(psg_process(participant_num, psg_path, psg_summary[0], psg_labels[0], trial_start, trial_end))
        print("Finished Processing")
    # Process Actiheart Sleep files
    actiheart_sleep_files = glob.glob(actiheart_path + "*sleep.xlsx")
    if len(actiheart_sleep_files) > 0:
        devices.append(process_actiheart_sleep(actiheart_sleep_files, trial_start, trial_end))

    # Process the Kubios Files
    kubios_path = psg_path + "Kubios Output/"
    med_hr = glob.glob(kubios_path + "*medium*.csv")
    # med_hr = []
    none_hr = glob.glob(kubios_path + "*none*.csv")
    if len(med_hr) > 0 and len(none_hr) > 0:
        print("Processing Kubios Output")
        kubios_med = read_kubios(med_hr[0], True, participant_num)
        kubios_none = read_kubios(none_hr[0], False, participant_num)
        kubios_hr = kubios_med.merge(kubios_none, how="inner", on='Time')
        kubios_hr = kubios_hr.loc[(kubios_hr['Time'] >= trial_start) & (kubios_hr['Time'] <= trial_end), :]
        devices.append(["Kubios", kubios_hr])
        kubios_hr.to_csv(kubios_path + "Test.csv", index=False)
        print("Finished")
    else:
        kubios_hr = pd.DataFrame()

    # Process the K5 Files
    k5_path = in_path + "/K5 data/"
    k5_files = glob.glob(k5_path + "/*_K5*")
    # k5_files = []
    if len(k5_files) > 0:
        print("BEGIN K5 PROCESSING")
        devices.append(process_k5(k5_files, k5_path, participant_num, trial_start, trial_end))
        print("FINISHED")
    print("Merging DataFrames")
    # Merge all dataframes into one
    align(devices, in_path, participant_num, protocol, activities, flags)
    print("Finished")
    print("Aggregating Data")
    agg_to_sec(devices, in_path, participant_num, protocol, activities, flags)

    print("ALL DONE")


def process_sleep():
    root = tk.Tk()
    root.winfo_toplevel().title("Select a Participant Folder")
    root.withdraw()
    # Start of dialogue
    print("Please select the folder of the participant you wish to process")
    path = filedialog.askdirectory()
    v_dir = "V:/R01 - W4K/1_Sleep Study/"
    if not os.path.isdir(v_dir):
        v_dir = "V:/ACOI/R01 - W4K/1_Sleep Study/"
    process_participant(path, v_dir, 'Sleep')

def process_all_sleep():
    root = tk.Tk()
    root.winfo_toplevel().title("Select directories")
    root.withdraw()
    # Start of dialogue
    print("Please select the folder housing all the participant folders you wish to process")
    home_dir = filedialog.askdirectory()
    files = glob.glob(home_dir + "/751[0-9]*[0-9]")
    # Get path to V drive
    v_dir = "V:/R01 - W4K/1_Sleep Study/"
    if not os.path.isdir(v_dir):
        v_dir = "V:/ACOI/R01 - W4K/1_Sleep Study/"
    # Process all participants:
    for file in files:
        process_participant(file, v_dir, 'Sleep')

def process_pa():
    root = tk.Tk()
    root.winfo_toplevel().title("Select a Participant Folder")
    root.withdraw()
    path = filedialog.askdirectory()
    v_dir = "V:/R01 - W4K/3_PA protocol/"
    if not os.path.isdir(v_dir):
        v_dir = "V:/ACOI/R01 - W4K/3_PA protocol/"
    process_participant(path, v_dir, 'PA')

def process_all_pa():
    root = tk.Tk()
    root.winfo_toplevel().title("Select directories")
    root.withdraw()
    # Start of dialogue
    print("Please select the folder housing all the participant folders you wish to process")
    home_dir = filedialog.askdirectory()
    files = glob.glob(home_dir + "/[0-9][0-9][0-9][0-9]")
    print(f"List of participants: {files}")
    # Get path to V drive
    v_dir = "V:/R01 - W4K/3_PA protocol/"
    if not os.path.isdir(v_dir):
        v_dir = "V:/ACOI/R01 - W4K/3_PA protocol/"
    # Process all participants:
    for file in files:
        process_participant(file, v_dir, 'PA')

def process_fl():
    root = tk.Tk()
    root.winfo_toplevel().title("Select a Participant Folder")
    root.withdraw()
    path = filedialog.askdirectory()
    v_dir = "V:/R01 - W4K/4_Free living/"
    if not os.path.isdir(v_dir):
        v_dir = "V:/ACOI/R01 - W4K/4_Free living/"
    process_participant(path, v_dir, 'FL-camp')
    process_participant(path, v_dir, 'FL-home')

if __name__ == "__main__":
    prot = int(input("Press 1 for Sleep. Press 2 for PA. Press 3 for Free Living: "))
    if prot == 1:
        process_sleep()
    elif prot == 2:
        process_pa()
    elif prot == 3:
        process_fl()
    else:
        print("INVALID INPUT DUMB-DUMB")
