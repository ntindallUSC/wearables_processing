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
        if not group_s.empty :
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
                     device + " Magnitude": [np.max, np.mean], device + " ENMO": [np.max, np.mean]}
    aggregated_data = data.groupby(device + " Time").agg(agg_functions)
    aggregated_data = aggregated_data.reset_index()
    aggregated_data.columns = [device + " Time", device + " RMS X", device + " Mean X", device + " RMS Y",
                               device + " Mean Y", device + " RMS Z", device + " Mean Z", device + " Max Magnitude",
                               device + " Mean Magnitude", device + " Max ENMO", device + " Mean ENMO"]
    return aggregated_data


# This function takes as input the aligned trial data
# It then calculates the MAD for actigraph, apple watch, and garmin.
# Next it aggregates all of the trial data to the second level.

def agg_to_sec(data, participant_num, path, devices):
    """
    :param data:
    :param participant_num:
    :param path:
    :return:
    """
    """
    Find and select the Wearable Data that is required for mad Calculation:
    """
    agg_devices = []
    for device in devices:
        # Remove microsecond from devices timestamp
        print(device)
        data[device + " Time"] = pd.to_datetime(data[device + " Time"]).apply(lambda x: x.replace(microsecond=0))
        # Find columns pertaining to device
        device_cols = get_columns(data, device)
        # Need to drop all blank rows. Also if the device is a garmin need to drop the reading number column
        if device != "Garmin":
            dev_data = data.iloc[:, device_cols[0]:device_cols[1]+1].dropna(how='all')
        else :
            dev_data = data.iloc[:, device_cols[0]:device_cols[1]+1].dropna(how='all').drop(columns=["Garmin Reading #"])
        # Calculate MAD
        dev_mad = calc_mad(dev_data, device)
        # Aggregate Rest
        dev_agg = aggregate_accel(dev_data, device)
        # Combine MAD and Aggregate data
        dev_agg = dev_agg.merge(dev_mad, how='left', left_on=device + ' Time', right_on=dev_mad.index)
        # Get device HR and merge with rest
        if device != "Actigraph":
            hr = [device + " Time", device + " Heart Rate", device + " HR Low", device + " HR High", device + " HR Change"]
            dev_hr = dev_data.loc[:, hr].dropna()
            dev_agg = dev_agg.merge(dev_hr, how='left', on=device + " Time")
        agg_devices.append(dev_agg)

    final_df = agg_devices[0].merge(agg_devices[1], how='left', left_on=devices[0] + " Time", right_on=devices[1] + " Time")
    if len(devices) > 2 :
        final_df = final_df.merge(agg_devices[2], how='left', left_on=devices[0] + " Time", right_on=devices[2] + " Time")

    final_df.rename(columns={"Actigraph Time": "Time"}, inplace=True)
    # agg_data = agg_data.drop(columns=['Garmin Time', 'Apple Time'])

    final_df.to_csv(path + "/" + participant_num + "_wearables_agg.csv",
                    index=False)
    return final_df