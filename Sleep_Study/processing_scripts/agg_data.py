import numpy as np
from datetime import timedelta
import pandas as pd

def calc_enmo(some_data):
    # Calculate the magnitue by first squaring all of the x, y, and z value, then summing them, and taking the square root.
    mag = ((some_data.applymap(lambda x: x ** 2)).sum(axis=1)).transform(lambda x: np.sqrt(x))
    # To calculate ENMO we subtract 1 (Gravity) from the vector magnitudes
    enmo = mag.transform(lambda x: x - 1)
    # Finally if we have any ENMO values less than 0 we round them up.
    enmo.loc[enmo.loc[:] < 0] = 0

    return mag, enmo

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
    # essentialy creates a window of agg_len, and interval of agg_len
    for i in range(int(trial_length // agg_len)):
        # print(end_time)
        # Get agg_len seconds worth of accelerometer readings
        group_s = some_data.loc[(some_data[time_name] >= start) & (some_data[time_name] <= end_time), :]
        # print(group_s)
        agg_s = group_s.aggregate(lambda x: np.mean(x))
        mag_s = agg_s[4]

        # print(f"{mag_s}")
        # Subtract the mean magnitude from each accelerometer magnitude from each vector magnitude and then take abs
        dif_mean = group_s[device + ' Magnitude'].apply(lambda x: abs(x - mag_s))
        # Caclulate the sum of all the vector mags - mean mags. Then divide by the number of vectors
        # print(dif_mean.sum())
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

def agg_to_sec(data, participant_num, path):
    """
    :param data:
    :param participant_num:
    :param path:
    :return:
    """
    """
    Find and select the Wearable Data that is required for mad Calculation:
    """

    data['Actigraph Time'] = data["Actigraph Time"].apply(lambda x: x.replace(microsecond=0))
    data['Garmin Time'] = (data["Garmin Time"].apply(pd.to_datetime)).apply(lambda x: x.replace(microsecond=0))
    data['Apple Time'] = (data["Apple Time"].apply(pd.to_datetime)).apply(lambda x: x.replace(microsecond=0))

    ac_cols = get_columns(data, "Actigraph")
    g_cols = get_columns(data, "Garmin")
    ap_cols = get_columns(data, "Apple")

    ac_data = data.iloc[:, ac_cols[0]:ac_cols[1] + 1].dropna(how='all')  # Actigraph
    # print(ac_data.columns)
    g_data = data.iloc[:, g_cols[0]:g_cols[1] + 1].dropna(how='all').drop(columns="Garmin Reading #")  # Garmin
    # print(g_data.columns)
    ap_data = data.iloc[:, ap_cols[0]:ap_cols[1] + 1].dropna(how='all')  # Apple
    # print(ap_data.columns)

    """
    Calculate MAD for the 3 devices:
    """
    ac_mad = calc_mad(ac_data, "Actigraph")
    g_mad = calc_mad(g_data, "Garmin")
    ap_mad = calc_mad(ap_data.drop(columns='Apple Heart Rate').dropna(), "Apple")

    """
    Aggregate Wearable  device accelerometer data to the second level
    """

    ac_agg = aggregate_accel(ac_data, "Actigraph")
    g_agg = aggregate_accel(g_data, "Garmin")
    # print(g_agg.columns)
    ap_agg = aggregate_accel(ap_data, "Apple")
    # print(ap_agg.columns)

    """ 
    Combine the aggregated accelerometer data with MAD calculations. Then combine with heart rate
    """
    # Combine aggregated Accelerometer data with MAD
    ac_agg = ac_agg.merge(ac_mad, how='left', left_on='Actigraph Time', right_on=ac_mad.index)
    g_agg = g_agg.merge(g_mad, how='left', left_on='Garmin Time', right_on=g_mad.index)
    ap_agg = ap_agg.merge(ap_mad, how='left', left_on='Apple Time', right_on=ap_mad.index)

    # Grab just garmin heart rate
    g_hr = g_data.loc[:, ["Garmin Time", "Garmin Heart Rate"]].dropna()
    # Combine Garmin accel with heart rate
    g_agg = g_agg.merge(g_hr, how="left", on="Garmin Time")

    # Grab jut apple heart rate
    ap_hr = ap_data.loc[:, ["Apple Time", "Apple Heart Rate"]].dropna()
    # Combine Apple accel with HR
    ap_agg = ap_agg.merge(ap_hr, how="left", on="Apple Time")

    """
    Select Actiheart Heart Rate and K5 data. Combine with aggregated wearable data.
    """

    # Combine Actigraph with Garmin
    agg_data = ac_agg.merge(g_agg, how="left", left_on="Actigraph Time", right_on="Garmin Time")
    # Combine Aggregated data with Apple
    agg_data = agg_data.merge(ap_agg, how="left", left_on="Actigraph Time", right_on="Apple Time")

    agg_data.rename(columns={"Actigraph Time": "Time"}, inplace=True)
    # agg_data = agg_data.drop(columns=['Garmin Time', 'Apple Time'])

    agg_data.to_csv(path + "/" + participant_num + "_wearables_agg.csv",
                    index=False)
    return agg_data