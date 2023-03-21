import pandas as pd
import mne
from datetime import timedelta
import glob
from os.path import exists, isdir


def edf_to_csv(input_path, output_path):
    # Reads in the edf file to a raw data object
    edf_data = mne.io.read_raw_edf(input_path)

    # Pull the data from the raw data object
    data = edf_data.get_data().T  # Numpy array

    # Create a dataframe from data.
    data_df = pd.DataFrame(data, columns=edf_data.ch_names)

    # Pull start date from the raw data object
    start_date = edf_data.info.get('meas_date')
    start_date = start_date.replace(tzinfo=None)

    # Pull sample rate from raw data object.
    sample_freq = edf_data.info.get('sfreq')
    time_between_samp = timedelta(seconds=(1 / sample_freq))

    # Create a timestamp for each reading
    timestamps = []
    for i in range(data_df.shape[0]):
        timestamp = start_date + i * time_between_samp
        timestamps.append(timestamp)

    # Add timestamps to data frame
    data_df.insert(0, 'Timestamps', timestamps)

    # Selects desired columns from data
    data_df = data_df[['Timestamps', 'EKG', 'EKG2', 'EKG3', 'PLETH']]
    # Output dataframe to file
    print("Writing to csv")
    data_df.to_csv(output_path, index=False)

def collect_files():
    sleep_path = "V:/ACOI/R01 - W4K/1_Sleep Study/1_Participant Data/"
    if not isdir(sleep_path):
        sleep_path = "V:/R01 - W4K/1_Sleep Study/1_Participant Data/"
    participants = glob.glob(sleep_path + "751[0-9][0-9]*")
    for participant in participants:
        # Get participant id
        participant_num = participant[-10:]
        # Get the file path to the data and the output
        edf_path = participant + "/PSG/" + participant_num + "_edf.edf"
        csv_path = participant + "/PSG/" + participant_num + "_rawPSG.csv"
        # Check if there is edf data, and that it hasn't already been processed
        if exists(edf_path) and not exists(csv_path):
            print(f"Data for {participant_num}")
            # Convert the edf dat to psg
            edf_to_csv(edf_path, csv_path)

