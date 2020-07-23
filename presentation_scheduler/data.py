import csv
import numpy as np
import matplotlib.pyplot as plt
from prettytable import PrettyTable
from datetime import datetime as date


#  load data from csv files
def load():
    slot_no = 300
    supervisor_no = 47
    presentation_no = 118
    preference_no = 3
    presentation_supervisor = np.zeros([presentation_no, supervisor_no], dtype=np.int8)
    supervisor_slot = np.zeros([supervisor_no, slot_no], dtype=np.int8)
    supervisor_preference = np.zeros([supervisor_no, 2 * preference_no], dtype=np.int8)

    # read supExaAssign.csv
    with open('input_files\SupExaAssign.csv') as file:
        csv_reader = csv.reader(file, delimiter=',')
        next(csv_reader)

        for row in csv_reader:
            i = int(row[0][1:]) - 1  # only underscores in P___ will be considered

            for col in range(1, 4):
                j = int(row[col][2:]) - 1  # only underscores in S0__ will be considered
                presentation_supervisor[i][j] = 1

    presentation_presentation = np.dot(presentation_supervisor, presentation_supervisor.transpose())
    # presentations supervised by same examiners are marked with 1
    presentation_presentation[presentation_presentation >= 1] = 1
    np.fill_diagonal(presentation_presentation, 0)  # mark diagonal with 0 so penalty points can be calculated correctly

    # read HC04.csv (staff unavailability)
    with open('input_files\HC04.csv') as file:
        csv_reader = csv.reader(file, delimiter=',')

        for row in csv_reader:
            i = int(row[0][2:]) - 1  # only underscores in S0__ will be considered
            j = [int(_) - 1 for _ in row[1:]]
            supervisor_slot[i][j] = 1

    slot_presentation = np.dot(supervisor_slot.transpose(), presentation_supervisor.transpose())
    slot_presentation[slot_presentation >= 1] = -1  # unavailable slots for presentation are marked with -1

    # read HC03.csv (venue unavailability)
    with open('input_files\HC03.csv') as file:
        csv_reader = csv.reader(file, delimiter=',')

        for row in csv_reader:
            i = [int(_) - 1 for _ in row[1:]]
            slot_presentation[i, :] = -1  # unavailable slots for presentation are marked with -1

    # read SC01.csv (consecutive presentations)
    with open('input_files\SC01.csv') as file:
        csv_reader = csv.reader(file, delimiter=',')

        for row in csv_reader:
            i = int(row[0][2:]) - 1  # only underscores in S0__ will be considered
            supervisor_preference[i][0] = int(row[1])

    # read SC02.csv (number of days)
    with open('input_files\SC02.csv') as file:
        csv_reader = csv.reader(file, delimiter=',')

        for row in csv_reader:
            i = int(row[0][2:]) - 1  # only underscores in S0__ will be considered
            supervisor_preference[i][1] = int(row[1])

    # read SC03.csv (change of venue)
    with open('input_files\SC03.csv') as file:
        csv_reader = csv.reader(file, delimiter=',')

        for row in csv_reader:
            i = int(row[0][2:]) - 1  # only underscores in S0__ will be considered
            supervisor_preference[i][2] = 1 if row[1] == "yes" else 0

    return slot_presentation, presentation_presentation, presentation_supervisor, supervisor_preference


# write result to csv file with timestamp
def write(slot_presentation, supervisor_preference, constraints_count, plot_data):
    timestamp = date.now().strftime("[%Y-%m-%d %H-%M-%S]")

    # plot graph
    title = (f"Improvement of Presentation Scheduling over Iterations\n"
             f"[Hard Constraints Violated:] {constraints_count[1]} "
             f"[Soft Constraints Violated:] {constraints_count[2]}\n"
             f"[Final Penalty Points:] {constraints_count[0]}")
    plt.title(title)
    plt.xlabel("Number of Iterations")
    plt.ylabel("Penalty Points")
    plt.axis([0, len(plot_data), 0, max(plot_data)])
    plt.plot(plot_data, "r--")
    plt.grid(True)
    plt.ioff()
    plt.show()
    graph_name = f"graph {timestamp}"
    plt.savefig(graph_name)

    # draw schedule
    venue_no = 4
    time_slot_no = 15
    day_slot_no = venue_no * time_slot_no
    day_no = 5
    slot_no = day_slot_no * day_no
    venues = ["Viva Room", "Meeting Room", "Interaction Room", "BJIM"]
    days = ["Mon", "Tues", "Wed", "Thu", "Fri"]

    schedule = PrettyTable()
    schedule.field_names = ["Day", "Venue",
                            "0900-0930", "0930-1000", "1000-1030",
                            "1030-1100", "1100-1130", "1130-1200",
                            "1200-1230", "1230-1300", "1400-1430",
                            "1430-1500", "1500-1530", "1530-1600",
                            "1600-1630", "1630-1700", "1700-1730"]

    venue = 0
    day = 0

    for first_slot in range(0, slot_no, time_slot_no):
        row = []

        if venue == 0:
            row.append(days[day])
        else:
            row.append("")

        row.append(venues[venue])

        for slot in range(first_slot, first_slot + time_slot_no):
            presentation = np.where(slot_presentation[slot] == 1)[0]

            if len(presentation) == 0:
                row.append("")
            else:
                presentation = presentation[0] + 1
                row.append("P" + str(presentation))

        schedule.add_row(row)
        venue += 1

        if venue == venue_no:
            venue = 0
            day += 1
            schedule.add_row([""] * (2 + time_slot_no))

    print("\n", schedule, "\n")

    # print supervisor-related data
    supervisor_no = supervisor_preference.shape[0]

    for supervisor in range(supervisor_no):
        venue_preference = "No" if supervisor_preference[supervisor][2] else "Yes"

        print(f"[Supervisor S{str(supervisor + 1).zfill(3)}] "
              f"[No. of Continuous Presentations: {supervisor_preference[supervisor][3]}] "
              f"[Day Preference: {supervisor_preference[supervisor][1]}] "
              f"[Days: {supervisor_preference[supervisor][4]}] "
              f"[Venue Change Preference: {venue_preference}] "
              f"[Venue Changes: {supervisor_preference[supervisor][5]}]")

    # write result data to csv file with timestamp
    filename = f"result {timestamp}.csv"

    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)

        for slot in range(slot_presentation.shape[0]):
            presentation = np.where(slot_presentation[slot] == 1)[0]

            if len(presentation) == 0:  # empty if no presentation is found for the slot
                writer.writerow(["null", ""])
            else:
                presentation = presentation[0] + 1  # Access x in array([x])
                writer.writerow(["P" + str(presentation), ""])
