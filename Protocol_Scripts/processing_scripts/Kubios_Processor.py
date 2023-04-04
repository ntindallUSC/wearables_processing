import pandas as pd
from datetime import datetime, timedelta


def read_kubios(path, filtered, part_num):
    # Opens file
    kubios = open(path)
    # The following variables are used to help locate the relevant data in the file.
    # header_num : The number of lines that precede our data
    header_num = 0
    # data_num : The number of lines of data
    data_num = -2  # Intialise at -2 because of the column names and blank file
    # data_found : a boolean used to represent when we've iterated to the data
    data_found = False
    # Iterate through file
    for line in kubios:
        # Time, is always the first line of our data.
        if "Time," in line:
            data_found = True
        if data_found:
            # INACTIVE signifies that we've reached the end of our data
            if "INACTIVE" in line:
                break
            else:
                data_num += 1
        else:
            header_num += 1

    kubios.close()
    kubios_data = pd.read_csv(path, skiprows=header_num, nrows=data_num, low_memory=False)

    # The data columns have leading white spaces, so I trim them and rename the columns of the data frame
    columns = []
    for name in kubios_data.columns:
        columns.append(name.strip())
    kubios_data.columns = columns
    # Select the 3 columns of interest
    kubios_data = kubios_data[["Time", "Effective data length.1", "Mean HR"]]
    # Drop the units row
    kubios_data.drop(index=0, inplace=True)
    kubios_data = kubios_data.applymap(lambda x: x.strip())
    # Convert length and mean hr to floats
    if filtered:
        kubios_data[['Effective data length.1', 'Mean HR']] = kubios_data[
            ['Effective data length.1', 'Mean HR']].applymap(lambda x: pd.to_numeric(x, errors='coerce'))
        kubios_data.rename(columns={"Effective data length.1": "Signal Quality of Heart Rate Estimation",
                                    "Mean HR": "Medium Mean HR"}, inplace=True)

    else:  # The data did not have filtering, therefor drop the effective length
        kubios_data.drop(columns="Effective data length.1", inplace=True)
        kubios_data['Mean HR'] = kubios_data['Mean HR'].apply(lambda x: pd.to_numeric(x, errors='coerce'))
        kubios_data.rename(columns={"Mean HR": "None Mean HR"}, inplace=True)
    # Convert time to datetime (Add date)
    date = datetime(year=int("20" + part_num[-2:]), month=int(part_num[-6:-4]), day=int(part_num[-4:-2]))
    kubios_data['Time'] = kubios_data['Time'].apply(
        lambda x: date + timedelta(hours=int(x[:2]), minutes=int(x[3:5]), seconds=int(x[6:8])))
    if 0 <= kubios_data['Time'].iloc[0].hour <= 6:
        kubios_data['Time'] = kubios_data['Time'].apply(lambda x: x + timedelta(hours=24))
    return kubios_data