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
    agg_functions = {device + " X": [rms], device + " Y": [rms], device + " Z": [rms], device + " Magnitude": [np.max],
                     device + " ENMO": [np.max]}
    aggregated_data = data.groupby(device + " Time").agg(agg_functions)
    aggregated_data = aggregated_data.reset_index()
    aggregated_data.columns = [device + " Time", device + " RMS X", device + " RMS Y", device + " RMS Z",
                               device + " Max Magnitude", device + " Max ENMO"]
    return aggregated_data


# This function takes as input the aligned trial data
# It then calculates the MAD for actigraph, apple watch, and garmin.
# Next it aggregates all of the trial data to the second level.

data = pd.read_csv("C:\\Users\\Nick\\Watch_Extraction\\Physical_Activity_Protocol\\Test_Data\\1854\\1854_aligned.csv",
                   low_memory=False)


def agg_to_sec(data, participant_num, path):
    """
    Find and select the Wearable Data that is required for mad Calculation:
    """

    ac_cols = get_columns(data, "Actigraph")
    g_cols = get_columns(data, "Garmin")
    ap_cols = get_columns(data, "Apple")

    ac_data = data.iloc[:, ac_cols[0]:ac_cols[1] + 1].dropna(how='all').drop(
        columns="Actigraph Second Fraction")  # Actigraph
    # print(ac_data.columns)
    g_data = data.iloc[:, g_cols[0]:g_cols[1] + 1]  # Garmin
    if not g_data.empty:
        g_data = g_data.dropna(how='all').drop(columns="Garmin Reading #")
    # print(g_data.columns)
    ap_data = data.iloc[:, ap_cols[0]:ap_cols[1] + 1].dropna(how='all').drop(columns="Apple Second Fraction")  # Apple
    # print(ap_data.columns)

    """
    Calculate MAD for the 3 devices:
    """
    ac_mad = calc_mad(ac_data, "Actigraph")
    if not g_data.empty:
        g_mad = calc_mad(g_data, "Garmin")
    ap_mad = calc_mad(ap_data.dropna(how='all'), "Apple")

    """
    Aggregate Wearable  device accelerometer data to the second level
    """

    ac_agg = aggregate_accel(ac_data, "Actigraph")
    if not g_data.empty:
        g_agg = aggregate_accel(g_data, "Garmin")
    # print(g_agg.columns)
    ap_agg = aggregate_accel(ap_data, "Apple")
    # print(ap_agg.columns)

    """ 
    Combine the aggregated accelerometer data with MAD calculations. Then combine with heart rate
    """
    # Combine aggregated Accelerometer data with MAD
    ac_agg = ac_agg.merge(ac_mad, how='left', left_on='Actigraph Time', right_on=ac_mad.index)
    if not g_data.empty:
        g_agg = g_agg.merge(g_mad, how='left', left_on='Garmin Time', right_on=g_mad.index)
    ap_agg = ap_agg.merge(ap_mad, how='left', left_on='Apple Time', right_on=ap_mad.index)

    if not g_data.empty:
        # Grab just garmin heart rate
        g_hr = g_data.loc[:, ["Garmin Time", "Garmin Heart Rate", "Garmin HR Low", "Garmin HR High", "Garmin HR Change"]].dropna()
        # Combine Garmin accel with heart rate
        g_agg = g_agg.merge(g_hr, how="left", on="Garmin Time")

    # Grab jut apple heart rate
    ap_hr = ap_data.loc[:, ["Apple Time", "Apple Heart Rate", "Apple HR Low", "Apple HR High", "Apple HR Change"]].dropna()
    # Combine Apple accel with HR
    ap_agg = ap_agg.merge(ap_hr, how="left", on="Apple Time")

    """
    Select Actiheart Heart Rate and K5 data. Combine with aggregated wearable data.
    """
    # Select Actiheart Data
    heart_data = data.loc[:, ["Activity", "Actiheart ECG Time", "Actiheart Heart Rate", "Actiheart HR Low",
                              "Actiheart HR High", "Actiheart HR Change"]].dropna()
    heart_data.rename(columns={"Actiheart ECG Time": "Time"}, inplace=True)
    heart_data["Time"] = heart_data["Time"].apply(pd.to_datetime)

    # Select K5 data
    k5_data = data.iloc[:, ap_cols[1] + 1:].dropna(how='all')
    k5_data['K5 t'] = k5_data['K5 t'].apply(pd.to_datetime)
    # Combine Actiheart Data with Actigraph Data
    agg_data = heart_data.merge(ac_agg, how="left", left_on="Time", right_on="Actigraph Time")
    if not g_data.empty:
        # Combine data with Garmin Data
        agg_data = agg_data.merge(g_agg, how="left", left_on="Time", right_on="Garmin Time")
    # Combine Data with Apple Data
    agg_data = agg_data.merge(ap_agg, how="left", left_on="Time", right_on="Apple Time")
    # Combine Data with K5 Data
    agg_data = agg_data.merge(k5_data, how="left", left_on="Time", right_on="K5 t")

    if not g_data.empty:
        agg_data = agg_data.drop(columns=['Actigraph Time', 'Garmin Time', 'Apple Time', 'K5 t'])
    else :
        agg_data = agg_data.drop(columns=['Actigraph Time', 'Apple Time', 'K5 t'])

    agg_data.to_csv(path + "/" + participant_num + "_agg.csv", index=False)
    return agg_data
