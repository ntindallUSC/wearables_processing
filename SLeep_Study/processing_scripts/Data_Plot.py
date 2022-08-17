from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt


def plot_accel(data, num, output):
    month = int(num[4:6])
    day = int(num[6:8])
    year = int("20" + num[8:])
    start = datetime(year=year, month=month, day=day, hour=20)
    end = start + timedelta(hours=10)
    # print(f"Start of sleep {start}\nEnd of sleep {end}")
    acti_seconds = data.loc[:, ["Time", "Actigraph Max ENMO", "Actigraph MAD"]].dropna()
    apple_seconds = data.loc[:, ["Time", "Apple Max ENMO", "Apple MAD"]].dropna()
    garmin_seconds = data.loc[:, ["Time", "Garmin Max ENMO", "Garmin MAD"]].dropna()

    # Plot ENMO
    fig, ax = plt.subplots(figsize=(25, 15))
    ax.plot(acti_seconds["Time"], acti_seconds["Actigraph Max ENMO"], label="Actigraph")
    ax.plot(apple_seconds["Time"], apple_seconds["Apple Max ENMO"], label="Apple")
    ax.plot(garmin_seconds["Time"], garmin_seconds["Garmin Max ENMO"], label="Garmin")
    ax.legend(fontsize="xx-large")
    ax.set(xlim=([start, end]))
    fig.savefig(output + num + "_ENMO.png")
    plt.close(fig)
    # Plot MAD
    fig, ax = plt.subplots(figsize=(25, 15))
    ax.plot(acti_seconds["Time"], acti_seconds["Actigraph MAD"], label="Actigraph")
    ax.plot(apple_seconds["Time"], apple_seconds["Apple MAD"], label="Apple")
    ax.plot(garmin_seconds["Time"], garmin_seconds["Garmin MAD"], label="Garmin")
    ax.legend(fontsize="xx-large")
    ax.set(xlim=([start, end]))
    fig.savefig(output + num + "_MAD.png")
    plt.close(fig)

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
def hr_helper(data, device, axis):
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