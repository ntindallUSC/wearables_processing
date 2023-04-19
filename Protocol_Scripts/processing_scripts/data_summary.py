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
import statsmodels.api as sm
from datetime import timedelta


# This function takes in wearable and flags implausible heart rate values.
def flag_hr(data, device, age, protocol='PA'):
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
    data.loc[data["Heart Rate"] >= (220 - age), ["HR High"]] = 1
    # Flags HR below threshold
    if protocol == "PA":
        data.loc[data["Heart Rate"] <= 60, ["HR Low"]] = 1
    elif protocol == "Sleep":
        data.loc[data["Heart Rate"] <= 50, ["HR Low"]] = 1
    # Calculate average HR of the last 8 seconds
    try:
        averaged = data[[time_name, 'Heart Rate']].rolling('8s', on=time_name, closed='left').mean()
    except:
        averaged = data[[time_name, 'Heart Rate']]
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
def hr_helper_sum(data, device, axis, start, end):
    if device == "Actiheart":
        time_name = "Time"
        p_color = "blue"
    elif device == "Apple":
        time_name = "Time"
        p_color = "orange"
    elif device == "Fitbit":
        time_name = 'Time'
        p_color = 'Red'
    else:
        time_name = "Time"
        p_color = "green"

    # flagged data
    flag = data
    # print(flag)
    flag = flag.loc[(flag["HR Change"] > 0) | (flag["HR Low"] > 0) | (flag["HR High"] > 0), [time_name, "Heart Rate"]]

    # Unflagged Data
    not_flag = data
    not_flag = not_flag.loc[
        (not_flag["HR Change"] == 0) | (not_flag["HR Low"] == 0) | (not_flag["HR High"] == 0), [time_name,
                                                                                                "Heart Rate"]]
    not_flag = not_flag[[time_name, "Heart Rate"]].dropna()

    axis.plot(not_flag[time_name], not_flag["Heart Rate"], color=p_color, label="Unflagged")
    axis.scatter(flag[time_name], flag["Heart Rate"], color=p_color, sizes=[100], edgecolor='k', label="Flagged")
    axis.set(xlim=[start, end])


# 0 Actigraph : Timestamp,Accelerometer X,Accelerometer Y,Accelerometer Z
# 1 Actiheart : ECG Time,Second Fraction,ECG (uV),X,Y,Z,Heart Rate,Upright Angle,Roll Angle
# 2 Apple : Time,Second Fraction,X,Y,Z,Heart Rate
# 3 Garmin : Time,Reading #,X,Y,Z,Heart Rate

# Here I create a dictionary that holds holds the name of each device and the sample rate of the accelerometer
stats = {
    0: ("Actigraph", 100),
    1: ("Actiheart", 50),
    2: ("Apple", 50),
    3: ("Garmin", 25),
    4: ("Fitbit", 50)
}


def summarize(device, path, data, start, end, fitabase=[]):
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

    # Convert accel to numeric
    data['X'] = pd.to_numeric(data['X'])
    data['Y'] = pd.to_numeric(data['Y'])
    data['Z'] = pd.to_numeric(data['Z'])

    if device >= 1:
        data['Heart Rate'] = pd.to_numeric(data['Heart Rate'])
        summary.write(
            data[["Time", "X", "Y", "Z", "Heart Rate"]].describe(datetime_is_numeric=True).to_string())
    else:
        summary.write(
            data[["Time", "X", "Y", "Z"]].describe(datetime_is_numeric=True).to_string())

    # Grab accelerometer and heart rate data from device if it has it
    accel = data.loc[(data['Time'] >= start) & (data['Time'] <= end), ["Time", "X", "Y", "Z"]].dropna(axis=0)
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
        hr_helper_sum(data, stats[device][0], ax, start, end)
        if len(fitabase) > 0:
            fita_hr = pd.read_csv(fitabase[0], parse_dates=['Time'])
            ax.plot(fita_hr['Time'], fita_hr['Value'], color='orange', label='Fitabase')
        ax.legend()
        plt.savefig(path + "_hr.png")
        plt.close()

    summary.close()


# A helper function that helps to plot the heart rate and flags
def hr_helper(data, device, axis):
    time_name = "Time"
    if device == "Actiheart":
        p_color = "blue"
    elif device == "Apple":
        p_color = "orange"
    elif device == "Garmin":
        p_color = "green"
    else:
        p_color = "Red"

    # flagged data
    flag = data
    flag = flag.loc[
        (flag[device + " HR Change"] > 0) | (flag[device + " HR Low"] > 0) | (flag[device + " HR High"] > 0), [
            time_name, device + " Mean Heart Rate"]]
    # Unflagged Data
    not_flag = data
    not_flag = not_flag.loc[(not_flag[device + " HR Change"] == 0) | (not_flag[device + " HR Low"] == 0) | (
            not_flag[device + " HR High"] == 0),
                            [time_name, device + " Mean Heart Rate"]]

    axis.plot(not_flag[time_name], not_flag[device + " Mean Heart Rate"], color=p_color,
              label=device + " Unflagged")
    axis.scatter(flag[time_name], flag[device + " Mean Heart Rate"], color=p_color, sizes=[100],
                 edgecolor='k', label=device + " Flagged")


# This function plots the heart rates of the wearables devices and  Actiheart vs Time all on the same plot.
# This function takes as input:
# The aligned dataframe, produced from pa_aligner.py
# A list of wearable devices
# The start and end time of the trial
# and a path to store the plot.
def plot_hr_pa(data, path, activities, k5):
    # Initialize plot used to plot heart rate
    fig_hr, ax_hr = plt.subplots(figsize=(25, 15))
    # Iterate through list of devices:
    for i in range(len(data.columns)):
        if " Mean Heart Rate" in data.columns[i]:
            temp_hr = data[data.columns[i:i + 4].insert(0, 'Time')].dropna()
            # Plot HR
            hr_helper(temp_hr, temp_hr.columns[1][:-16], ax_hr)

    # Set axes for HR fig
    ax_hr.legend(fontsize="xx-large")
    ax_hr.set(ylim=[60, 220])
    for key in activities:
        ax_hr.annotate(activities[key][0], xy=(mdates.date2num(activities[key][1]), 0), xycoords='data',
                       xytext=(mdates.date2num(activities[key][1]), 55), textcoords='data', annotation_clip=False,
                       horizontalalignment='center')
    # Save figure
    fig_hr.savefig(path + "_hr_fig.png")

    # Read in k5 data
    if "K5 VO2/Kg" in data.columns:
        k5_data = data[["Time", "K5 VO2/Kg"]].dropna(axis=0)
        # Create new axis for data
        ax_o2kg = ax_hr.twinx()
        # Plot K5 VO2/KG
        ax_o2kg.plot(k5_data['Time'], k5_data['K5 VO2/Kg'], label="V02/kg", color='purple')
        fig_hr.savefig(k5)
    plt.close('all')


def plot_hr(data, path, part_num, protocol, rem_flags=False):
    if protocol == 'Sleep':
        if "Kubios Medium Mean HR" in data.columns:
            for device in data.columns:
                if " Mean Heart Rate" in device:
                    hr = data[[device, "Kubios Medium Mean HR"]].dropna()
                    # Plot a bland altman plot
                    fig, ax = plt.subplots(figsize=(10, 8))
                    sm.graphics.mean_diff_plot(hr[device], hr["Kubios Medium Mean HR"], ax=ax)
                    plt.savefig(path + "/" + part_num + "_" + device[:-16] + "_ba.jpg", bbox_inces='tight')
                    plt.close(fig)
    elif protocol[:2] == "FL":
        if "Actiheart Mean Heart Rate" in data.columns:
            for device in data.columns:
                if " Mean Heart Rate" in device and "Actiheart" not in device:
                    if rem_flags is False:
                        hr = data[[device, "Actiheart Mean Heart Rate"]].dropna()
                        out_path = path + "/" + part_num + "_" + device[:-16] + "_ba.jpg"
                    else:
                        hr = data.loc[(data["Actiheart HR Low"] == 0) & (data["Actiheart HR High"] == 0) & (data["Actiheart HR Change"] == 0), [device, "Actiheart Mean Heart Rate"]].dropna()
                        out_path = path + "/" + part_num + "_" + device[:-16] + "_ba_no_flags.jpg"
                    # Plot a bland altman plot
                    fig, ax = plt.subplots(figsize=(10, 8))
                    sm.graphics.mean_diff_plot(hr[device], hr["Actiheart Mean Heart Rate"], ax=ax)
                    plt.savefig(out_path, bbox_inces='tight')
                    plt.close(fig)


# This function plots the ENMO and MAD for each wearable device.
def plot_accel(data, path, protocol='PA', activities=None, flags=None):
    device_color = {"Actigraph": "blue", "Apple": "orange", "Garmin": "green", "Fitbit": "red"}
    # Initialize 2 plots. One for ENMO and one for MAD.
    fig, ax = plt.subplots(figsize=(25, 15))
    fig2, ax2 = plt.subplots(figsize=(25, 15))
    # Plot MAX ENMO and MAD per second
    for device in data.columns:
        if " Max ENMO" in device:
            ax.plot(data['Time'], data[device], label=device[:-9], color=device_color[device[:-9]])

        if " MAD" in device:
            temp = data[["Time", device]].dropna()
            ax2.plot(temp["Time"], temp[device], label=device[:-4], color=device_color[device[:-4]])

    # Set ax for ENMO fig
    ax.legend(fontsize="xx-large")
    # Add activity name
    if protocol == "PA":
        for key in activities:
            ax.annotate(activities[key][0], xy=(mdates.date2num(activities[key][1]), 0), xycoords='data',
                        xytext=(mdates.date2num(activities[key][1]), -4), textcoords='data', annotation_clip=False,
                        horizontalalignment='center')

    # Set ax for MAD fig
    ax2.legend(fontsize="xx-large")
    if protocol == "PA":
        # Add activity name labels
        for key in activities:
            ax2.annotate(activities[key][0], xy=(mdates.date2num(activities[key][1]), 0), xycoords='data',
                         xytext=(mdates.date2num(activities[key][1]), -3), textcoords='data', annotation_clip=False,
                         horizontalalignment='center')

    # Save both figures
    fig.savefig(path + "_ENMO_fig.png")
    fig2.savefig(path + "_MAD_fig.png")
    # Close both figures
    plt.close('all')


# Takes as input a dataframe containing 3 columns, corresponding to the axis of an accelerometer for a device.
def calc_enmo(some_data):
    # Calculate the magnitue by first squaring all of the x, y, and z value, then summing them, and taking the square root.
    mag = ((some_data.applymap(lambda x: x ** 2)).sum(axis=1)).transform(lambda x: np.sqrt(x))
    # To calculate ENMO we subtract 1 (Gravity) from the vector magnitudes
    enmo = mag.transform(lambda x: x - 1)
    # Finally if we have any ENMO values less than 0 we round them up.
    enmo.loc[enmo.loc[:] < 0] = 0

    return mag, enmo
