import pandas as pd
from datetime import timedelta
import numpy as np
from .data_summary import plot_accel, plot_hr_pa, plot_hr
from .merge_data import add_activity_lables

accelerometers = ["Fitbit", 'Apple', "Garmin", "Actigraph"]
gt_hr = ["Actiheart", "Kubios"]
labels = ["K5"]
# Function that takes as input the aligned data from a PA trial.
# It returns the 1st and last column index for a device. EX: returns index of all Garmin Columns
# Remove microsecond from timestamps
def micro_remove(a_time):
    if not pd.isnull(a_time):
        a_time = a_time.replace(microsecond=0)
    return a_time

def add_column_names(a_data, a_device):
    a_list = []
    for column in a_data.columns:
        a_list.append(a_device + " " + column)
    return a_list

def drop_time_columns(some_data):
    cols_to_drop = []
    for col in some_data.columns[1:]:
        if "Time" in col:
            cols_to_drop.append(col)
    return cols_to_drop

def calc_mad(some_data, device):
    all_mad = {}

    time_name = "Time"
    # Grab the first timestamp from data
    #some_data[time_name] = some_data[time_name].apply(pd.to_datetime)
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
            dif_mean = group_s['Magnitude'].apply(lambda x: abs(x - mag_s))
            # Calculate the sum of all the vector mags - mean mags. Then divide by the number of vectors
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

    mad_df = pd.Series(data=all_mad, name = "MAD")
    return mad_df


# This function aggregates a wearables accelerometer data to the second level.
# It takes the RMS of each accelerometer reading and the max of the vector magnitude and ENMO
def calc_accel_metrics(data, device):
    # Initialize function to calculate rms
    rms = lambda x: np.sqrt(np.mean(x ** 2))
    # Specify what function to use on each column:
    agg_functions = {"X": [rms, np.mean], "Y": [rms, np.mean], "Z": [rms, np.mean],
                     "Magnitude": [np.max, np.mean, rms], "ENMO": [np.max, np.mean, rms]}
    aggregated_data = data.groupby("Time").agg(agg_functions)
    aggregated_data = aggregated_data.reset_index()
    aggregated_data.columns = ["Time", "RMS X", "Mean X", "RMS Y",
                               "Mean Y", "RMS Z", "Mean Z", "Max Magnitude",
                               "Mean Magnitude", "RMS Magnitude", "Max ENMO",
                               "Mean ENMO", "RMS ENMO"]
    return aggregated_data

def agg_accelerometers(data, device):
    accel_cols = ['Time', "X", "Y", "Z", "Magnitude", "ENMO"]

    data["Time"] = data["Time"].apply(micro_remove)
    accel_data = data[accel_cols].dropna()
    accel_metrics = calc_accel_metrics(accel_data, device)
    accel_mad = calc_mad(accel_data, device)
    return accel_metrics.merge(accel_mad, how='left', left_on='Time', right_on=accel_mad.index)

def agg_hr(data, device):
    hr_cols = ['Time', 'Heart Rate', "HR Low", 'HR High', "HR Change"]
    if device != 'Kubios' and device != 'Garmin':
        data["Time"] = data["Time"].apply(micro_remove)

    if device == 'Kubios':
        hr_cols = ['Time', 'Signal Quality of Heart Rate Estimation', 'Medium Mean HR', 'None Mean HR']
        hr_data = data.loc[:, hr_cols]
    else :
        agg_functions = {"Heart Rate": [np.mean], "HR Low": [max], "HR High": [max], "HR Change": [max]}
        hr_data = data[hr_cols].dropna().groupby(hr_cols[0], as_index=False).agg(agg_functions).reset_index()
        hr_data.columns = ['index', 'Time', 'Mean Heart Rate', 'HR Low', 'HR High', 'HR Change']
        hr_data.drop(columns=['index'], inplace=True)

    return hr_data

def agg_labels(data):
    data = data.dropna()
    for column in data.columns[1:]:
        data[column] = pd.to_numeric(data[column], errors='coerce')
    label_data = data.groupby(data.columns[0], as_index=False).mean()
    return label_data

# This function takes as input the aligned trial data
# It then calculates the MAD for actigraph, apple watch, and garmin.
# Next it aggregates all of the trial data to the second level.
def agg_to_sec(devices, path, participant_num, protocol="Sleep", activities=None, flags=None):
    """
    Find and select the Wearable Data that is required for mad Calculation:
    """
    aggregate_data = []
    for device in devices:
        print(f"Device: {device[0]}")
        if device[0] in accelerometers:
            aggregate_data.append(agg_accelerometers(device[1], device[0]))
            # Merge Heart rate with accelerometer. ALl accelerometers but Actigraph have HR
            if device[0] != "Actigraph":
                aggregate_data[-1] = aggregate_data[-1].merge(agg_hr(device[1], device[0]), on="Time", how='left')
        elif device[0] in gt_hr:
            aggregate_data.append(agg_hr(device[1], device[0]))
        elif device[0] in labels:
            aggregate_data.append(agg_labels(device[1]))
        elif device[0] == 'PSG' or device[0] == "Actiheart Sleep":
            aggregate_data.append(device[1])
        aggregate_data[-1].columns = add_column_names(aggregate_data[-1], device[0])

    merged_data = aggregate_data.pop(0)
    for device in aggregate_data:
        merged_data = merged_data.merge(device, left_on=merged_data.columns[0], right_on=device.columns[0], how='left')
    #agg_data.drop(columns=time_drop, inplace=True)
    merged_data.drop_duplicates(inplace=True)
    merged_data.drop(columns=drop_time_columns(merged_data), inplace=True)
    merged_data.rename(columns={merged_data.columns[0] : 'Time'}, inplace=True)

    # Plot ACCELEROMETERS
    plot_accel(merged_data, path + "/" + participant_num, protocol, activities, flags)
    # Plot HR
    if protocol == "PA":
        plot_hr_pa(merged_data, path + "/" + participant_num, activities, path + "/K5 data/Processed Data/" + participant_num + "_v02.png")
    else:
        plot_hr(merged_data, path, participant_num, protocol)
        if protocol[:2] == "FL":
            plot_hr(merged_data, path, participant_num, protocol, True)

    if protocol == 'PA':
        merged_data = add_activity_lables(merged_data, activities, flags)
    merged_data.to_csv(path + "/" + participant_num + "_agg.csv", index=False)

