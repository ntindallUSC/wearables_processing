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
    # Report number of Flags found in actiheart
    if device == 1:
        flags = trial.loc[trial['BPM Flag'] == 1, 'BPM Flag'].dropna(axis=0)

        summary.write(f"{len(flags)} Heart Rate readings either below 60 or above 220\n\n")

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
    plt.clf()

    if device >= 1:
        plt.figure(figsize=(25, 15))
        hr = trial.loc[:, ['Time', 'Heart Rate']].dropna(axis=0)
        hr["Heart Rate"] = hr["Heart Rate"].replace(['0', 0], np.nan)
        plt.plot(hr['Time'], hr['Heart Rate'], label="Heart Rate")
        plt.legend()
        plt.xlim([start, end])
        plt.ylim([60, 220])
        plt.savefig(path + "_hr.png")
        plt.clf()

    summary.close()


# This function plots the heart rates of Garmin, Apple Watches, and Actiheart vs Time all on the same plot.
# This function takes as input:
# The aligned dataframe, produced from pa_aligner.py
# The start and end time of the trial
# and a path to store the plot.
def plot_hr(data, start, end, activities, path):
    # Grab the actiheart data
    acti_hr = data.loc[(data['Actiheart ECG Time'] >= start) & (data['Actiheart ECG Time'] <= end),
                       ["Actiheart ECG Time", "Actiheart Heart Rate"]].dropna(axis=0)
    # Grab the apple data
    apple_hr = data.loc[(data['Apple Time'] >= start) & (data['Apple Time'] <= end),
                        ["Apple Time", "Apple Heart Rate"]].dropna(axis=0)
    # Grab the Garmin data
    garmin_hr = data.loc[(data['Garmin Time'] >= start) & (data['Garmin Time'] <= end),
                         ["Garmin Time", "Garmin Heart Rate"]].dropna(axis=0)

    # Create figure
    fig, ax = plt.subplots(figsize=(25, 15))
    # Plot Actigraph Data
    acti_hr["Actiheart Heart Rate"] = acti_hr["Actiheart Heart Rate"].replace(['0', 0], np.nan)
    ax.plot(acti_hr['Actiheart ECG Time'], acti_hr['Actiheart Heart Rate'], label="ACTI Heart")
    # Plot Apple Data
    ax.plot(apple_hr['Apple Time'], apple_hr['Apple Heart Rate'], label="Apple")
    # Plot Garmin Data
    ax.plot(garmin_hr['Garmin Time'], garmin_hr['Garmin Heart Rate'], label="Garmin")
    ax.legend(fontsize="xx-large")
    ax.set(xlim=([start, end]), ylim=[60, 220])
    for key in activities:
        ax.annotate(activities[key][0], xy=(mdates.date2num(activities[key][1]), 0), xycoords='data',
                    xytext=(mdates.date2num(activities[key][1]), 55), textcoords='data', annotation_clip=False,
                    horizontalalignment='center')

    fig.savefig(path + "_hr_fig.png")
    fig.clf()


# This function calculates the RMS of each second for 1 axis on 3 devices (Garmin, Apple Watch, Actigraph)
# It then plots the RMS values versus time
# It takes as input the aligned data, the start and end time of the trial,
# Which accelerometer axis it will be working with, and a path to store the plots.
def plot_accel(data, start, end, axis, activities, path):
    # Grab the actigraph data
    data.loc[:, "Actigraph Timestamp"] = pd.to_datetime(data["Actigraph Timestamp"])
    acti_accel = data.loc[(data['Actigraph Timestamp'] >= start) & (data['Actigraph Timestamp'] < end),
                          ["Actigraph Timestamp", "Actigraph Accelerometer " + axis]].dropna(axis=0)
    acti_accel['Actigraph Accelerometer ' + axis] = pd.to_numeric(acti_accel['Actigraph Accelerometer ' + axis])

    # Calculate the rms for each second
    acti_seconds = acti_accel.groupby("Actigraph Timestamp").aggregate(lambda x: np.sqrt(np.sum(x ** 2)))

    data.loc[:, "Apple Time"] = pd.to_datetime(data["Apple Time"])
    apple_accel = data.loc[
        (data['Apple Time'] >= start) & (data['Apple Time'] < end), ["Apple Time", "Apple " + axis]].dropna(axis=0)
    apple_accel['Apple ' + axis] = pd.to_numeric(apple_accel['Apple ' + axis])
    # Calculate the rms for each second
    apple_seconds = apple_accel.groupby("Apple Time").aggregate(lambda x: np.sqrt(np.sum(x ** 2)))

    # Grab Garmin Data
    data.loc[:, "Garmin Time"] = pd.to_datetime(data["Garmin Time"])
    garmin_accel = data.loc[(data['Garmin Time'] >= start) & (data['Garmin Time'] < end),
                            ["Garmin Time", "Garmin " + axis]].dropna(axis=0)
    garmin_accel['Garmin ' + axis] = pd.to_numeric(garmin_accel['Garmin ' + axis])
    # Garmin data is measured on a different scale. Need to convert.
    garmin_accel.loc[:, 'Garmin ' + axis] = garmin_accel["Garmin " + axis].apply(lambda x: x / 1000)

    # Calculate the rms for each second
    garmin_seconds = garmin_accel.groupby("Garmin Time").aggregate(lambda x: np.sqrt(np.sum(x ** 2)))

    # Plot each accelerometer vs time
    fig, ax = plt.subplots(figsize=(25, 15))
    ax.plot(acti_seconds.index, acti_seconds['Actigraph Accelerometer ' + axis], label='Actigraph ' + axis)
    ax.plot(apple_seconds.index, apple_seconds['Apple ' + axis], label="Apple " + axis)
    ax.plot(garmin_seconds.index, garmin_seconds['Garmin ' + axis], label='Garmin ' + axis)
    ax.legend(fontsize="xx-large")
    ax.set(xlim=([start, end]))
    for key in activities:
        ax.annotate(activities[key][0], xy=(mdates.date2num(activities[key][1]), 0), xycoords='data',
                    xytext=(mdates.date2num(activities[key][1]), -4), textcoords='data', annotation_clip=False,
                    horizontalalignment='center')

    fig.savefig(path + "_accel" + axis + "_fig.png")
    fig.clf()
