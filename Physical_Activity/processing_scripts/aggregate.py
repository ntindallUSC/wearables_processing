import pandas as pd
from datetime import timedelta
import numpy as np


# Function that takes as input the aligned data from a PA trial.
# It returns the 1st and last column index for a device. EX: returns index of all Garmin Columns
def get_columns(data, device):
    data_heads = data.columns
    device_cols = [100, 0]
    count = 0
    for column in data_heads:
        if device in column:
            if device_cols[0] > count:
                device_cols[0] = count
            if device_cols[1] < count:
                device_cols[1] = count

        count += 1
    return device_cols

def calc_mad(some_data, device):
    all_mad = {}

    time_name = device + " Time"
    # Grab the first timestamp from data
    some_data[time_name] = some_data[time_name].apply(pd.to_datetime)
    start = some_data.loc[some_data.index[0], time_name]
    # Specify the amount of time to aggregate over
    agg_len = 5
    # Grab end of aggregation period
    end_time = start + timedelta(seconds=agg_len - 1)
    # Calculate the total length of the trial in seconds
    trial_length = (some_data.loc[some_data.index[-1], time_name] - start).total_seconds()
    # Runs the total length of trial divided by the length of time we aggregate over
    # essentially creates a window of agg_len, and interval of agg_len
    for i in range(int(trial_length // agg_len)):
        # print(end_time)
        # Get agg_len seconds worth of accelerometer readings
        group_s = some_data.loc[(some_data[time_name] >= start) & (some_data[time_name] <= end_time), :]
        if not group_s.empty:
            # print(group_s)
            # Get the mean X, Y, and Z of those readings
            agg_s = group_s.aggregate(lambda x: np.mean(x))
            mag_s = agg_s[4]
            # print(f"{mag_s}")
            # Subtract the mean magnitude from each accelerometer magnitude from each vector magnitude and then take abs
            dif_mean = group_s[device + ' Magnitude'].apply(lambda x: abs(x - mag_s))
            # Caclulate the sum of all the vector mags - mean mags. Then divide by the number of vectors
            # print(dif_mean.sum())
            # if device == "Apple":
                # print(group_s)
                # print(dif_mean.shape[0])
            mad = (dif_mean.sum()) / dif_mean.shape[0]
            # print(mad)

            # Add each Mad and the corresponding time to a list :
            all_mad[end_time] = mad
            #
            start = end_time + timedelta(seconds=1)
            end_time = start + timedelta(seconds=agg_len - 1)

    mad_df = pd.Series(data=all_mad, name = device + " MAD")
    return mad_df


# This function aggregates a wearables accelerometer data to the second level.
# It takes the RMS of each accelerometer reading and the max of the vector magnitude and ENMO
def aggregate_accel(data, device):
    # Initialize function to calculate rms
    rms = lambda x: np.sqrt(np.mean(x ** 2))
    # Specify what function to use on each column:
    agg_functions = {device + " X": [rms, np.mean], device + " Y": [rms, np.mean], device + " Z": [rms, np.mean],
                     device + " Magnitude": [np.max, np.mean, rms], device + " ENMO": [np.max, np.mean, rms]}
    aggregated_data = data.groupby(device + " Time").agg(agg_functions)
    aggregated_data = aggregated_data.reset_index()
    aggregated_data.columns = [device + " Time", device + " RMS X", device + " Mean X", device + " RMS Y",
                               device + " Mean Y", device + " RMS Z", device + " Mean Z", device + " Max Magnitude",
                               device + " Mean Magnitude", device + " RMS Magnitude", device + " Max ENMO",
                               device + " Mean ENMO", device + " RMS ENMO"]
    return aggregated_data


# This function takes as input the aligned trial data
# It then calculates the MAD for actigraph, apple watch, and garmin.
# Next it aggregates all of the trial data to the second level.
def agg_to_sec(data, devices, participant_num, path):
    """
    Find and select the Wearable Data that is required for mad Calculation:
    """
    wearables = []
    for device in devices:
        # Get a subset of the data's columns containing the wearables devices data
        dev_cols = get_columns(data, device)
        # Drop a column depending on the device
        if device != "Garmin":
            dev_data = data.iloc[:, dev_cols[0]:dev_cols[1] + 1].dropna(how='all').drop(columns=device + " Second Fraction")
        elif device == "Garmin":
            dev_data = data.iloc[:, dev_cols[0]:dev_cols[1] + 1].dropna(how='all').drop(columns=device + " Reading #")

        # Calculate MAD for the device
        dev_mad = calc_mad(dev_data, device)

        # Calculate the RMS and Mean of raw acceleration data. Calculate the max and mean of Magnitude and ENMO
        dev_agg = aggregate_accel(dev_data, device)

        # Combine aggregated Accelerometer data with MAD
        dev_agg = dev_agg.merge(dev_mad, how='left', left_on=device + ' Time', right_on=dev_mad.index)
        # Combine aggregated accelerometer values with heart rate. (Actigraph doesn't collect heart rate)
        if device != "Actigraph":
            dev_hr = dev_data.loc[:, [device + " Time", device + " Heart Rate", device + " HR Low", device + " HR High", device + " HR Change"]].dropna()
            dev_hr = dev_hr.groupby(device + " Time").agg(np.mean).reset_index()
            # Combine Apple accel with HR
            dev_agg = dev_agg.merge(dev_hr, how="left", on=device + " Time")
        # Add data to list of wearable data
        wearables.append(dev_agg)

    """
    Select Actiheart Heart Rate and K5 data. Combine with aggregated wearable data.
    """
    # Select Actiheart Data
    heart_data = data.loc[:, ["Activity", "Flags", "Actiheart ECG Time", "Actiheart Heart Rate", "Actiheart HR Low",
                              "Actiheart HR High", "Actiheart HR Change"]].dropna(subset=['Actiheart Heart Rate'])
    heart_data.rename(columns={"Actiheart ECG Time": "Time"}, inplace=True)
    heart_data["Time"] = heart_data["Time"].apply(pd.to_datetime)

    # Select K5 data
    k5_cols = get_columns(data, "K5")
    k5_data = data.iloc[:, k5_cols[0]:k5_cols[1]].dropna(how='all')
    k5_data['K5 t'] = k5_data['K5 t'].apply(pd.to_datetime)
    k5_data = k5_data.groupby('K5 t').agg(np.mean)
    # k5_data = k5_data.reset_index()
    # print(k5_data)


    # Combine Actiheart Data with wearables Data
    agg_data = heart_data.merge(wearables[0], how="left", left_on="Time", right_on=devices[0] + " Time")
    # combine with rest of wearables data
    device = 1
    while device < len(devices) :
        agg_data = agg_data.merge(wearables[device], how="left", left_on="Time", right_on=devices[device] + " Time")
        device += 1

    # Combine Data with K5 Data
    agg_data = agg_data.merge(k5_data, how="left", left_on="Time", right_on=k5_data.index)

    # Only keep 1 time column. (the time column from the actiheart data
    time_drop = []
    for device in devices :
        time_drop.append(device + " Time")
    agg_data.drop(columns=time_drop, inplace=True)
    agg_data.drop_duplicates(inplace=True)

    agg_data.to_csv(path + "/" + participant_num + "_agg.csv", index=False)
    return agg_data
