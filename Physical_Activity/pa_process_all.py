import glob
import os
from pa_processor import process_participant


# Intialize path to folder containing all the participant files
parent_dir = "V:\\R01 - W4K\\3_PA protocol\\"
if not os.path.isdir(parent_dir) :
    parent_dir = "V:\\ACOI\\R01 - W4K\\3_PA protocol\\"

# Create a list of all the participant files
participants = glob.glob(parent_dir + "1_Participants\\[0-9][0-9][0-9][0-9]")
# Process all participants
i = 1
total_participants = len(participants)
print(total_participants)


for participant in participants:
    print(f"PROCESSING {i}/{total_participants}")
    print(f"Participant {participant[-4:]}")
    # Process the Apple, Garmin, and Actigraph Data
    process_participant(participant, parent_dir)

    i += 1