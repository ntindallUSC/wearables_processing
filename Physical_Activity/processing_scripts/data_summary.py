"""
This file defines a function that takes as input:
    device: which is an integer used to represent which device is being summarized
    path: which is the output path of the function
    data: a dataframe of sensor data
    start: the start time of the trial
    end: the end time of the trial

The function then selects a subset of the dataframe where all the sensor data was recorded during the trial.
The function then counts the amount of sensor readings, outputs it to a text file, and
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import timedelta

# This function takes in wearable and flags implausible heart rate values.
def flag_hr(data, device, age):
    time_name = "Time"
    # Select only the HR data and corresponding time
    data = data[[time_name, 'Heart Rate']].dropna()
    # Get rid of microseconds if there are any
    data[time_name] = data[time_name].apply(lambda x: x.replace(microsecond=0))
    # Insert flags 3 cases:
    # HR to high
    data.insert(2, "HR High", 0)
    # HR to low
    data.insert(3, "HR Low", 0)
    # To big of a change in HR
    data.insert(4, "HR Change", 0)
    # Flags HR over threshold
    data.loc[data["Heart Rate"] >= (220-age), ["HR High"]] = 1
    # Flags HR below threshold
    data.loc[data["Heart Rate"] <= 60, ["HR Low"]] = 1
    # Calculate average HR of the last 8 seconds
    averaged = data[[time_name,'Heart Rate']].rolling('8s', on=time_name, closed='left').mean()
    # Insert temporary column to keep track of average chang of hr
    data.insert(5, "Average BPM Change", averaged['Heart Rate'])
    # Subract the average HR of the last 8 seconds from it's corresponding current HR
    data['Average BPM Change'] = data["Heart Rate"] - data["Average BPM Change"]
    # Make all the values Non-Negative
    data['Average BPM Change'] = data['Average BPM Change'].apply(abs)
    # If the value is greater than or equal to 5, flag it
    data.loc[data["Average BPM Change"] >= 10, "HR Change"] = 1
    # Drop the subtracted columns
    data.drop(columns=["Average BPM Change"], inplace=True)
    return data

# A helper function that helps to plot the heart rate and flags
def hr_helper_sum(data, device, axis):
    if device == "Actiheart":
        time_name = "Time"
        p_color = "blue"
    elif device == "Apple":
        time_name = "Time"
        p_color = "orange"
    else:
        time_name = "Time"
        p_color = "green"

    # flagged data
    flag = data
    # print(flag)
    flag = flag.loc[(flag["HR Change"] == 1) | (flag["HR Low"] == 1), [time_name, "Heart Rate"]]

    # Unflagged Data
    not_flag = data
    not_flag.loc[(not_flag["HR Change"] == 1) | (not_flag["HR Low"] == 1), ["Heart Rate"]] = np.nan
    not_flag = not_flag[[time_name, "Heart Rate"]].dropna()

    axis.plot(not_flag[time_name], not_flag["Heart Rate"], color=p_color, label= "Unflagged")
    axis.scatter(flag[time_name], flag["Heart Rate"], color=p_color, sizes=[100], edgecolor='k', label= "Flagged")


# 0 Actigraph : Timestamp,Accelerometer X,Accelerometer Y,Accelerometer Z
# 1 Actiheart : ECG Time,Second Fraction,ECG (uV),X,Y,Z,Heart Rate,Upright Angle,Roll Angle
# 2 Apple : Time,Second Fraction,X,Y,Z,Heart Rate
# 3 Garmin : Time,Reading #,X,Y,Z,Heart Rate

# Here I create a dictionary that holds holds the name of each device and the sample rate of the accelerometer
stats = {
    0: ("Actigraph", 100),
    1: ("Actiheart", 50),
    2: ("Apple", 50),
    3: ("Garmin", 25)
}


def summarize(device, path, data, start, end):
    # Initialize output text file for summary:
    summary = open(path + "_summary.txt", 'w')

    # Write few lines to summary:
    summary.write(f"{stats[device][0]} Summary\nTrial Start {start}\nTrial End {end}\n")
    # Calculate the number of sensor readings that should be present
    length = (end - start)  # Length of trial
    accel_num = stats[device][1] * length.total_seconds()  # Sample Rate * Length of Trial in Seconds
    # Write to information to file
    if device == 2:
        summary.write(
            f"Trial Length {length}\n\nThe device collects at {str(stats[device][1])} hz. There should be {accel_num} "
            + f"readings for this trial. \nIf the device produces a heart rate reading every 5 seconds there should be {length.total_seconds() // 5}"
            + f" Heart rate readings\n\n")

    elif device >= 1:
        summary.write(
            f"Trial Length {length}\n\nThe device collects at {str(stats[device][1])} hz. There should be {accel_num} "
            + f"readings for this trial. \nIf the device produces a heart rate reading each second there should be {length.total_seconds()}"
            + f" Heart rate readings.\n\n")
    else:
        summary.write(
            f"Trial Length {length}\n\nThe device collects at {str(stats[device][1])} hz. There should be {accel_num} " +
            f"readings for this trial.\n\n")

    # Rename the time column to time
    data = data.rename(columns={data.columns[0]: "Time"})
    # Now rename actigraph columns to match rest of devices
    if device == 0:
        data.rename(columns={data.columns[2]: "X", data.columns[3]: "Y", data.columns[4]: "Z"}, inplace=True)
    # First select the data specific to the trial
    trial = data.loc[(data['Time'] >= start) & (data['Time'] <= end)]

    # Convert accel to numeric
    trial.loc[:, 'X'] = pd.to_numeric(trial['X'])
    trial.loc[:, 'Y'] = pd.to_numeric(trial['Y'])
    trial.loc[:, 'Z'] = pd.to_numeric(trial['Z'])


    if device >= 1:
        trial.loc[:, 'Heart Rate'] = pd.to_numeric(trial['Heart Rate'])
        summary.write(
            trial.loc[:, ["Time", "X", "Y", "Z", "Heart Rate"]].describe(datetime_is_numeric=True).to_string())
    else:
        summary.write(
            trial.loc[:, ["Time", "X", "Y", "Z"]].describe(datetime_is_numeric=True).to_string())

    # Grab accelerometer and heart rate data from device if it has it
    accel = trial.loc[:, ["Time", "X", "Y", "Z"]].dropna(axis=0)
    # Plot accelerometer data
    plt.figure(figsize=(25, 15))
    plt.plot(accel['Time'], accel['X'], label="X")
    plt.plot(accel['Time'], accel['Y'], label="Y")
    plt.plot(accel['Time'], accel['Z'], label="Z")
    plt.legend()
    plt.xlim([start, end])
    plt.savefig(path + "_xyz.png")
    plt.close()

    if device >= 1:
        fig, ax = plt.subplots(figsize=(25, 15))
        hr_helper_sum(trial, stats[device][0], ax)
        ax.legend()
        plt.savefig(path + "_hr.png")
        plt.close()

    summary.close()


# A helper function that helps to plot the heart rate and flags
def hr_helper(data, device, axis):
    if device == "Actiheart":
        time_name = "ECG Time"
        p_color = "blue"
    elif device == "Apple":
        time_name = "Time"
        p_color = "orange"
    else:
        time_name = "Time"
        p_color = "green"

    # flagged data
    flag = data
    flag = flag.loc[(flag[device + " HR Change"] == 1) | (flag[device + " HR Low"] == 1), [device + " " + time_name, device + " Heart Rate"]]
    # Unflagged Data
    not_flag = data
    not_flag.loc[(not_flag[device + " HR Change"] == 1) | (not_flag[device + " HR Low"] == 1), [device + " Heart Rate"]] = np.nan

    axis.plot(not_flag[device + " " + time_name], not_flag[device + " Heart Rate"], color=p_color, label=device + " Unflagged")
    axis.scatter(flag[device + " " + time_name], flag[device + " Heart Rate"], color=p_color, sizes=[100], edgecolor='k', label= device + " Flagged")

# This function plots the heart rates of Garmin, Apple Watches, and Actiheart vs Time all on the same plot.
# This function takes as input:
# The aligned dataframe, produced from pa_aligner.py
# The start and end time of the trial
# and a path to store the plot.
def plot_hr(data, start, end, activities, path, k5):
    # Grab the actiheart data
    acti_hr = data.loc[(data['Actiheart ECG Time'] >= start) & (data['Actiheart ECG Time'] <= end),
                       ["Actiheart ECG Time", "Actiheart Heart Rate", "Actiheart HR Low", "Actiheart HR High",
                        "Actiheart HR Change"]].dropna(axis=0)
    # Grab the apple data
    apple_hr = data.loc[(data['Apple Time'] >= start) & (data['Apple Time'] <= end),
                        ["Apple Time", "Apple Heart Rate", "Apple HR High", "Apple HR Low", "Apple HR Change"]].dropna(axis=0)
    # Grab the Garmin data
    if "Garmin Time" in data.columns:
        garmin_hr = data.loc[(data['Garmin Time'] >= start) & (data['Garmin Time'] <= end),
                             ["Garmin Time", "Garmin Heart Rate", "Garmin HR High", "Garmin HR Low", "Garmin HR Change"]].dropna(axis=0)
    else:
        garmin_hr = pd.DataFrame()

    k5_data = data.loc[(data['K5 t'] >= start) & (data['K5 t'] <= end),
                       ["K5 t", "K5 VO2/Kg"]].dropna(axis=0)

    # Create figure
    fig, ax = plt.subplots(figsize=(25, 15))
    # Plot Actigraph Data
    hr_helper(acti_hr, "Actiheart", ax)
    # Plot Apple Data
    hr_helper(apple_hr, "Apple", ax)
    # Plot Garmin Data
    if garmin_hr.shape[0] > 0:
        hr_helper(garmin_hr, "Garmin", ax)
    ax.legend(fontsize="xx-large")
    ax.set(xlim=([start, end]), ylim=[60, 220])
    for key in activities:
        ax.annotate(activities[key][0], xy=(mdates.date2num(activities[key][1]), 0), xycoords='data',
                    xytext=(mdates.date2num(activities[key][1]), 55), textcoords='data', annotation_clip=False,
                    horizontalalignment='center')

    fig.savefig(path + "_hr_fig.png")
    plt.close(fig)

    # Now I will plot a figure with 2 Y-axes, the first displaying V02/kg and the second displaying heart rate
    fig, ax1 = plt.subplots(figsize=(25, 15))
    ax1.plot(k5_data['K5 t'], k5_data['K5 VO2/Kg'], label="V02/kg")
    ax1.legend(fontsize="xx-large")
    ax1.set(xlim=([start, end]), ylim=[0, 100])
    ax2 = ax1.twinx()
    ax2.plot(acti_hr['Actiheart ECG Time'], acti_hr['Actiheart Heart Rate'], label="ACTI Heart")
    ax2.plot(apple_hr['Apple Time'], apple_hr['Apple Heart Rate'], label="Apple")
    if garmin_hr.shape[0] > 0:
        ax2.plot(garmin_hr['Garmin Time'], garmin_hr['Garmin Heart Rate'], label="Garmin")
    # fig.tight_layout()
    for key in activities:
        ax1.annotate(activities[key][0], xy=(mdates.date2num(activities[key][1]), 0), xycoords='data',
                     xytext=(mdates.date2num(activities[key][1]), -4), textcoords='data', annotation_clip=False,
                     horizontalalignment='center')

    fig.savefig(k5)
    plt.close(fig)

#This function plots the ENMO and MAD for each wearable device.
def plot_accel(data, start, end, activities, path):
    # Select
    acti_seconds = data.loc[:, ["Time", "Actigraph Max ENMO", "Actigraph MAD"]].dropna()
    apple_seconds = data.loc[:, ["Time", "Apple Max ENMO", "Apple MAD"]].dropna()
    if "Garmin Max ENMO" in data.columns:
        garmin_seconds = data.loc[:, ["Time", "Garmin Max ENMO", "Garmin MAD"]].dropna()
    else:
        garmin_seconds= pd.DataFrame()

    # Plot each accelerometer vs time
    fig, ax = plt.subplots(figsize=(25, 15))
    ax.plot(acti_seconds["Time"], acti_seconds['Actigraph Max ENMO'], label='Actigraph')
    ax.plot(apple_seconds["Time"], apple_seconds['Apple Max ENMO'], label="Apple")
    if not garmin_seconds.empty:
        ax.plot(garmin_seconds["Time"], garmin_seconds['Garmin Max ENMO'], label='Garmin')
    ax.legend(fontsize="xx-large")
    ax.set(xlim=([start, end]))
    for key in activities:
        ax.annotate(activities[key][0], xy=(mdates.date2num(activities[key][1]), 0), xycoords='data',
                    xytext=(mdates.date2num(activities[key][1]), -4), textcoords='data', annotation_clip=False,
                    horizontalalignment='center')

    fig.savefig(path + "_ENMO_fig.png")
    plt.close(fig)

    # Plot each accelerometer vs time
    fig, ax = plt.subplots(figsize=(25, 15))
    ax.plot(acti_seconds["Time"], acti_seconds['Actigraph MAD'], label='Actigraph')
    ax.plot(apple_seconds["Time"], apple_seconds['Apple MAD'], label="Apple")
    if garmin_seconds.shape[0] > 0:
        ax.plot(garmin_seconds["Time"], garmin_seconds['Garmin MAD'], label='Garmin')
    ax.legend(fontsize="xx-large")
    ax.set(xlim=([start, end]))
    for key in activities:
        ax.annotate(activities[key][0], xy=(mdates.date2num(activities[key][1]), 0), xycoords='data',
                    xytext=(mdates.date2num(activities[key][1]), -3), textcoords='data', annotation_clip=False,
                    horizontalalignment='center')

    fig.savefig(path + "_MAD_fig.png")
    plt.close(fig)

# Takes as input a dataframe containing 3 columns, corresponding to the axis of an accelerometer for a device.
def calc_enmo(some_data):
    # Calculate the magnitue by first squaring all of the x, y, and z value, then summing them, and taking the square root.
    mag = ((some_data.applymap(lambda x: x ** 2)).sum(axis=1)).transform(lambda x: np.sqrt(x))
    # To calculate ENMO we subtract 1 (Gravity) from the vector magnitudes
    enmo = mag.transform(lambda x: x - 1)
    # Finally if we have any ENMO values less than 0 we round them up.
    enmo.loc[enmo.loc[:] < 0] = 0

    return mag, enmo

