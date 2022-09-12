import glob
from pa_processor import process_participant


# Intialize path to folder containing all the participant files
parent_dir = "V:\\R01 - W4K\\3_PA protocol\\1_Participants"

# Create a list of all the participant files
participants = glob.glob(parent_dir + "\\[0-9][0-9][0-9][0-9]")
# Process all participants
i = 1
total_participants = len(participants)
print(total_participants)

for participant in participants:
    print(f"PROCESSING {i}/{total_participants}")
    print(f"Participant {participant[-4:]}")
    # Process the Apple, Garmin, and Actigraph Data
    process_participant(participant)

    i += 1