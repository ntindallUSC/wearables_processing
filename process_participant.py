import argparse
from Protocol_Scripts import process_protocol, edf_convert

parser = argparse.ArgumentParser(prog='W4K_Processing', description='A program that is used to process W4K protocols')

# Add a parameter that specifies which protocol to process. Currently 2 options: Sleep or PA
parser.add_argument("protocol", help='Indicates which protocol is being processed. should be either sleep or pa')
# Add parameter that specifies number of participants to be processed
parser.add_argument('-m', '--multiple', action='store_true',
                    help='If included will process all participants in a folder')
parser.add_argument('-edf', '--edf_files', action='store_true', help='If this parameter is present all of the edf files that have not been converted to csv files will be converted to csv files.')

args = parser.parse_args()


if args.protocol == "sleep":
    if args.edf_files:
        edf_convert.collect_files()
    elif args.multiple:
        process_protocol.process_all_sleep()
    else:
        process_protocol.process_sleep()
elif args.protocol == 'pa':
    if args.multiple:
        process_protocol.process_all_pa()
    else:
        process_protocol.process_pa()
elif args.protocol == 'fl':
    process_protocol.process_fl()

else:
    raise ValueError("INVALID ARGUMENT. python process_participant.py MUST BE FOLLOWED BY sleep OR pa OR fl")
