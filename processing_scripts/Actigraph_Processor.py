import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import os


def actigraph_process(participant_num, acti_path, acti_data, acti_folder):
    print("BEGIN ACTIGRAPH PROCESSING")
    # Read in the actigraph data
    actigraph = pd.read_csv(acti_data[0], skiprows=10)
    actigraph_np = actigraph.to_numpy()

    # I define this function to convert actigraph time stamps to datetime datatype. I will use this function when I iterate
    # through the actigraph data.
    def actigraph_time_convert(aTime):
        a = datetime.datetime.strptime(aTime, '%m/%d/%Y %H:%M:%S.%f')
        return a
    output_path = os.path.join(acti_folder, "Processed Data")
    if os.path.isdir(output_path) is False:
        os.mkdir(output_path)

    # ----------------------------------------------------------------------------------------------------------------
    # Give a brief summary of the actigraph data
    # Write start of actigraph data
    acti_summ = open(output_path + "\\" + participant_num + "_Data_Summary.txt", 'w')
    start_time = actigraph_time_convert(actigraph.iloc[0, 0])
    acti_summ.write(f"Start Time: {start_time}\n")

    # Write end of actigraph data
    end_time = actigraph_time_convert(actigraph.iloc[-1, 0])
    acti_summ.write(f"End Time: {end_time}\n")

    # Write total length of time measured
    total_time = end_time - start_time
    acti_summ.write(f"Total Time Ran: {total_time}\n")

    # Calculate sample rate and compare to known sample rate.
    readings_num = actigraph.shape[0]

    time_interval = total_time / readings_num
    acti_summ.write(f"The total number of readings is {readings_num}\n")
    acti_summ.write(f"The interval between each reading is {time_interval}\n")

    # -----------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # Need get a subset of the actigraph data that begins at 8pm the night of the experiment and ends at 6am the day after
    # First I need to initialize the target start time and the end start time. The date comes from participant number
    date = (int("20" + participant_num[-2:]), int(participant_num[-6:-4]), int(participant_num[-4:-2]))
    sleep_start = datetime.datetime(year=date[0], month=date[1], day=date[2], hour=20)
    start_found = False
    start_index = 0
    sleep_end = datetime.datetime(year=date[0], month=date[1], day=date[2], hour=6) + datetime.timedelta(days=1)
    end_found = False
    end_index = 0

    i = 0
    while end_found is False:
        if sleep_start <= actigraph_time_convert(actigraph_np[i, 0]) and start_found is False:
            start_index = i
            start_found = True
        if start_found:
            if actigraph_time_convert(actigraph_np[i, 0]) <= sleep_end:
                end_index = i
            if actigraph_time_convert(actigraph_np[i, 0]) >= sleep_end:
                end_found = True
        i += 1

    over_night = pd.DataFrame(actigraph_np[start_index:end_index + 1, :], columns=['Time', 'X', 'Y', 'Z'])

    over_night['Time'] = over_night["Time"].apply(lambda x: actigraph_time_convert(x))
    over_night['Time'] = pd.to_datetime(over_night["Time"])


    print("BEGIN PLOTTING")
    plt.figure(figsize=(25, 15))
    plt.plot(over_night['Time'], over_night['X'], label="X")
    plt.plot(over_night['Time'], over_night['Y'], label="Y")
    plt.plot(over_night['Time'], over_night['Z'], label="Z")
    plt.legend()
    plt.xlim([over_night.iloc[0, 0], over_night.iloc[-1, 0]])
    plt.savefig(output_path + "\\" + participant_num + "_xyz.png")

    acti_summ.write("\n8PM to 6AM Summary: \n\n")
    acti_summ.write(over_night.loc[:, ["X","Y","Z"]].describe().to_string())
    acti_summ.close()
    print("ACTIGRAPH FINISHED")
    # ------------------------------------------------------------------------------------------------------------------
