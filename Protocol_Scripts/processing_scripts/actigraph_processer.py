import pandas as pd
from datetime import datetime
from .data_summary import calc_enmo

def time_convert(a_time):
    return datetime.strptime(a_time, '%m/%d/%Y %H:%M:%S.%f')

def process_actigraph(data_paths, start, end) :
    # Read in file and store it as a dataframe.
    actigraph_data = pd.read_csv(data_paths[0], skiprows=11, names=["Time", "X", "Y", "Z"], parse_dates=['Time'],
                                 date_parser=time_convert)
    actigraph_data = actigraph_data.loc[(actigraph_data['Time'] >= start) & (actigraph_data['Time'] <= end), :]
    sec_frac = actigraph_data["Time"].apply(lambda x: x.microsecond)
    actigraph_data.insert(1, 'Second Fraction', sec_frac)
    mag, enmo = calc_enmo(actigraph_data.loc[:, ['X', 'Y', 'Z']])
    actigraph_data.insert(5, "Magnitude", mag)
    actigraph_data.insert(6, "ENMO", enmo)
    return ["Actigraph", actigraph_data]