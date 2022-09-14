from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.dates as mdates


def plot_accel(data, num, devices, output):
    # Get date and star time of sleep
    month = int(num[4:6])
    day = int(num[6:8])
    year = int("20" + num[8:])
    start = datetime(year=year, month=month, day=day, hour=20)
    end = start + timedelta(hours=10)

    # Initialize plots
    fig_1, ax_1 = plt.subplots(figsize=(25, 15))
    fig_2, ax_2 = plt.subplots(figsize=(25, 15))
    # Plot all devices
    i = 0
    while i < len(devices):
        # Grab data
        dev_seconds = data.loc[:, ["Time", devices[i] + " Max ENMO", devices[i] + " MAD"]].dropna()
        # Plot ENMO
        ax_1.plot(dev_seconds["Time"], dev_seconds[devices[i] + " Max ENMO"], label=devices[i])
        # Plot MAD
        ax_2.plot(dev_seconds["Time"], dev_seconds[devices[i] + " MAD"], label=devices[i])
        i += 1

    # Save and close ENMO figure
    ax_1.legend(fontsize="xx-large")
    ax_1.set(xlim=([start, end]))
    fig_1.savefig(output + num + "_ENMO.png")
    plt.close(fig_1)
    # Save and close MAD figure
    ax_2.legend(fontsize="xx-large")
    ax_2.set(xlim=([start, end]))
    fig_2.savefig(output + num + "_MAD.png")
    plt.close(fig_2)

# This function takes in wearable and flags implausible heart rate values.
def flag_hr(data, device, age):
    time_name = "Time"
    # Select only the HR data and corresponding time
    data = data[[time_name, 'Heart Rate']].dropna()
    # Get rid of microseconds if there are any
    # data[time_name] = data[time_name].apply(lambda x: x.replace(microsecond=0))
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
def hr_helper(data, device, axis, kubios):
    if device == "Actiheart":
        time_name = "Time"
        p_color = "blue"
    elif device == "Apple":
        time_name = "Time"
        p_color = "orange"
    else:
        time_name = "Time"
        p_color = "green"
    if kubios is False :
        # flagged data
        flag = data
        # print(flag)
        flag = flag.loc[(flag["HR Change"] == 1) | (flag["HR Low"] == 1), [time_name, "Heart Rate"]]

        # Unflagged Data
        not_flag = data
        not_flag.loc[(not_flag["HR Change"] == 1) | (not_flag["HR Low"] == 1), ["Heart Rate"]] = np.nan
        not_flag = not_flag[[time_name, "Heart Rate"]].dropna()

        axis.plot(not_flag[time_name], not_flag["Heart Rate"], color=p_color, label= device + " Unflagged")
        axis.scatter(flag[time_name], flag["Heart Rate"], color=p_color, sizes=[100], edgecolor='k', label= device + " Flagged")
    else :
        time_name = device + " " + time_name
        # flagged data
        flag = data
        # print(flag)
        flag = flag.loc[(flag[device + " HR Change"] == 1) | (flag[device + " HR Low"] == 1), [time_name, device + " Heart Rate"]]

        # Unflagged Data
        not_flag = data
        not_flag.loc[(not_flag[device + " HR Change"] == 1) | (not_flag[device + " HR Low"] == 1), [device + " Heart Rate"]] = np.nan
        not_flag = not_flag[[time_name, device + " Heart Rate"]].dropna()

        axis.plot(not_flag[time_name], not_flag[device + " Heart Rate"], color=p_color, label=device + " Unflagged")
        axis.scatter(flag[time_name], flag[device + " Heart Rate"], color=p_color, sizes=[100], edgecolor='k',
                     label=device + " Flagged")

# This function plots the heart rates of Garmin, Apple Watches, and Actiheart vs Time all on the same plot.
# This function takes as input:
# The aligned dataframe, produced from pa_aligner.py
# The start and end time of the trial
# and a path to store the plot.
def plot_hr(data, path, part_num):
    # Grab Kubios Heart Rate
    kubios_hr = data.loc[:, ["Time", "Kubios Medium Mean HR"]].dropna(axis=0)
    # Grab the apple data
    apple_hr = data.loc[:, ["Apple Time", "Apple Heart Rate", "Apple HR High", "Apple HR Low", "Apple HR Change"]].dropna(axis=0)
    # Grab the Garmin data
    if "Garmin Time" in data.columns:
        garmin_hr = data.loc[:, ["Garmin Time", "Garmin Heart Rate", "Garmin HR High", "Garmin HR Low", "Garmin HR Change"]].dropna(axis=0)
    else:
        garmin_hr = pd.DataFrame()

    # Create figure
    fig, ax = plt.subplots(figsize=(25, 15))
    # Plot Actigraph Data
    ax.plot(kubios_hr['Time'], kubios_hr["Kubios Medium Mean HR"], color="blue", label="Kubios")
    # Plot Apple Data
    hr_helper(apple_hr, "Apple", ax, True)
    # Plot Garmin Data
    if garmin_hr.shape[0] > 0:
        hr_helper(garmin_hr, "Garmin", ax, True)
    ax.legend(fontsize="xx-large")
    # ax.set(ylim=[40, 220])
    print(path)
    fig.savefig(path + "/" + part_num + "_hr_fig.png")
    plt.close(fig)