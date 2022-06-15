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
    if device > 1:
        summary.write(
            f"Trial Length {length}\n\nThe device collects at {str(stats[device][1])} hz. There should be {accel_num} "
            + f"readings for this trial. \nIf the device produces a heart rate reading each second there should be {length.total_seconds()}"
            + f" Heart rate readings\n\n")
    elif device == 1 :
        summary.write(
            f"Trial Length {length}\n\nThe device collects at {str(stats[device][1])} hz. There should be {accel_num} "
            + f"readings for this trial. \nIf the device produces a heart rate reading each second there should be {length.total_seconds()//5}"
            + f" Heart rate readings\n\n")
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
        summary.write(trial.loc[:, ["Time", "X", "Y", "Z", "Heart Rate"]].describe(datetime_is_numeric=True).to_string())
    else :
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
        hr = trial[['Time', 'Heart Rate']].dropna(axis=0)
        plt.plot(hr['Time'], hr['Heart Rate'], label="Heart Rate")
        plt.legend()
        plt.xlim([start, end])
        plt.savefig(path + "_hr.png")
        plt.clf()

    summary.close()
