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

bad_bois = ["0967", "1991", "2007", "2454", "2455", "2456", "2458", "2495", "2497", "2500", "2503", "2504", "2506",
            "2508", "2531", "2533", "2541", "2543", "2546", "2557", "2559", "2560", "2566"]
for participant in participants:
    print(f"PROCESSING {i}/{total_participants}")
    print(f"Participant {participant[-4:]}")
    # Process the Apple, Garmin, and Actigraph Data
    if participant in bad_bois :
        process_participant(participant)

    i += 1