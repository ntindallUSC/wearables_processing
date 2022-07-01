from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

def plot_accel(apple, garmin, actigraph, num, axis, output):
    month = int(num[4:6])
    day = int(num[6:8])
    year = int("20" + num[8:])
    start = datetime(year=year, month=month, day=day, hour=20)
    end = start + timedelta(hours=10)
    # print(f"Start of sleep {start}\nEnd of sleep {end}")

    # Grab Apple data and then calculate RMS for each second
    apple = apple.loc[(apple['Time'] >= start) & (apple['Time'] <= end), ["Time", axis]].dropna(axis=0)
    # Converts accelerometer values from string to number
    apple[axis] = pd.to_numeric(apple[axis])
    # Removes the seconds and microseconds from time
    apple["Time"] = apple["Time"].apply(lambda x: x.replace(microsecond=0))
    # Groups the data at minute level and then calculates the RMS
    apple_seconds = apple.groupby("Time").aggregate(lambda x: np.sqrt(np.mean(x**2)))

    # Grab Garmin data and then calculate RMS for each second
    garmin = garmin.loc[(garmin['Time'] >= start) & (garmin['Time'] <= end), ["Time", axis]].dropna(axis=0)
    # Converts accelerometer values from string to number
    garmin[axis] = pd.to_numeric(garmin[axis])
    # Groups Data by minutes and then calculates the rms
    garmin_seconds = garmin.groupby("Time").aggregate(lambda x: np.sqrt(np.mean((x/1000)**2))) # Divide by 1000 to convert garmin to similar units

    # Grab Actigraph data and then calculate RMS for each second
    actigraph = actigraph.loc[(actigraph["Timestamp"] >= start) & (actigraph["Timestamp"] <= end), ["Timestamp", "Accelerometer " + axis]].dropna(axis=0)
    # Convert accelerometer values from string to number
    actigraph["Accelerometer " + axis] = pd.to_numeric(actigraph["Accelerometer " + axis])
    # Removes seconds and microseconds from time
    actigraph["Timestamp"] = actigraph["Timestamp"].apply(lambda x: x.replace(microsecond=0))
    # Group data by minutes and then calculate the rms for each minute
    actigraph_seconds = actigraph.groupby("Timestamp").aggregate(lambda x: np.sqrt(np.mean(x**2)))

    fig, ax = plt.subplots(figsize=(25, 15))

    ax.plot(actigraph_seconds.index, actigraph_seconds["Accelerometer " + axis], label= "Actigraph")
    ax.plot(apple_seconds.index, apple_seconds[axis], label="Apple")
    ax.plot(garmin_seconds.index, garmin_seconds[axis], label="Garmin")
    ax.legend(fontsize="xx-large")
    ax.set(xlim=([start, end]))
    fig.savefig(output + num + "_" + axis+".png")
    plt.close(fig)

