
import csv
import os
import traci
import joblib

CONFIG_FILE = "intersection.sumocfg"
MODEL_FILE = "congestion_model.pkl"
TLS_ID = "J17"

TRAFFIC_FILE = os.environ.get("TRAFFIC_FILE", "traffic.rou.xml")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "adaptive_traffic_data.csv")
END_TIME = 600

SEED = os.environ.get("SEED", "42")
TRIPINFO_FILE = os.environ.get(
    "TRIPINFO_FILE", "tripinfo_adaptive.xml"
)
ROUTE_FILE = os.environ.get("ROUTE_FILE", "routes_adaptive.xml")

MIN_GREEN = 15
MAX_GREEN = 45

GREEN_PHASES = [0, 2]
YELLOW_PHASES = [1, 3]
YELLOW_DURATION = 3

QUEUE_THRESHOLD = 5
GREEN_ADJUSTMENT = 5

model = joblib.load(MODEL_FILE)

def get_phase_queue(phase_index):
    controlled_links = traci.trafficlight.getControlledLinks(TLS_ID)
    phase_state = traci.trafficlight.getAllProgramLogics(TLS_ID)[0].phases[
        phase_index
    ].state

    lanes = set()

    for index, signal in enumerate(phase_state):
        if signal in ("G", "g") and index < len(controlled_links):
            for link in controlled_links[index]:
                if link:
                    lanes.add(link[0])

    return sum(
        traci.lane.getLastStepHaltingNumber(lane)
        for lane in lanes
        if not lane.startswith(":")
    )

def get_congestion_prediction():
    vehicles = traci.vehicle.getIDList()
    vehicle_count = len(vehicles)

    lanes = [
        lane for lane in traci.lane.getIDList()
        if not lane.startswith(":")
    ]

    queue_length = sum(
        traci.lane.getLastStepHaltingNumber(lane)
        for lane in lanes
    )

    if vehicle_count > 0:
        average_speed = sum(
            traci.vehicle.getSpeed(vehicle)
            for vehicle in vehicles
        ) / vehicle_count

        waiting_time = sum(
            traci.vehicle.getWaitingTime(vehicle)
            for vehicle in vehicles
        )
    else:
        average_speed = 0
        waiting_time = 0

    features = [[
        vehicle_count,
        queue_length,
        average_speed,
        waiting_time
    ]]

    prediction = model.predict(features)[0]

    return (
        vehicle_count,
        queue_length,
        average_speed,
        waiting_time,
        prediction
    )

def calculate_green_time(current_phase, queue_current, queue_other, prediction):
    green_time = 30

    if queue_current > queue_other:
        green_time += GREEN_ADJUSTMENT
    elif queue_other > queue_current:
        green_time -= GREEN_ADJUSTMENT

    if prediction > 0:
        green_time += GREEN_ADJUSTMENT
    elif prediction < 0:
        green_time -= GREEN_ADJUSTMENT

    return max(MIN_GREEN, min(MAX_GREEN, green_time))

traci.start([
    "sumo-gui",
    "-c", CONFIG_FILE,
    "--route-files", TRAFFIC_FILE,
    "--seed", SEED,
    "--tripinfo-output", TRIPINFO_FILE,
    "--vehroute-output", ROUTE_FILE
])

try:
    with open(OUTPUT_FILE, "w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "time",
            "vehicle_count",
            "queue_length",
            "average_speed",
            "waiting_time",
            "congestion_prediction",
            "current_phase",
            "green_duration"
        ])

        current_green_duration = 30
        green_start_time = 0
        last_phase = -1

        while traci.simulation.getTime() < END_TIME:
            traci.simulationStep()

            current_time = traci.simulation.getTime()
            current_phase = traci.trafficlight.getPhase(TLS_ID)

            (
                vehicle_count,
                queue_length,
                average_speed,
                waiting_time,
                prediction
            ) = get_congestion_prediction()

            if current_phase in GREEN_PHASES:
                if current_phase != last_phase:
                    green_start_time = current_time

                    queue_current = get_phase_queue(current_phase)
                    other_phase = 2 if current_phase == 0 else 0
                    queue_other = get_phase_queue(other_phase)

                    current_green_duration = calculate_green_time(
                        current_phase,
                        queue_current,
                        queue_other,
                        prediction
                    )

                    print(
                        f"Time: {current_time:.0f}s | "
                        f"Phase: {current_phase} | "
                        f"Current queue: {queue_current} | "
                        f"Other queue: {queue_other} | "
                        f"Green duration: {current_green_duration}s"
                    )

                elapsed_green = current_time - green_start_time

                if elapsed_green >= current_green_duration:
                    yellow_phase = YELLOW_PHASES[
                        GREEN_PHASES.index(current_phase)
                    ]
                    traci.trafficlight.setPhase(TLS_ID, yellow_phase)

                last_phase = current_phase

            elif current_phase in YELLOW_PHASES:
                yellow_elapsed = current_time - green_start_time

                if yellow_elapsed >= current_green_duration + YELLOW_DURATION:
                    next_green = 2 if current_phase == 1 else 0
                    traci.trafficlight.setPhase(TLS_ID, next_green)
                    last_phase = -1

            writer.writerow([
                current_time,
                vehicle_count,
                queue_length,
                round(average_speed, 2),
                round(waiting_time, 2),
                prediction,
                current_phase,
                current_green_duration
            ])

    remaining_vehicles = traci.vehicle.getIDCount()
    pending_vehicles = len(traci.simulation.getPendingVehicles())
    unfinished_vehicles = remaining_vehicles + pending_vehicles

    print("\nAdaptive simulation completed successfully!")
    print("Traffic input:", TRAFFIC_FILE)
    print("Traffic data saved to:", OUTPUT_FILE)
    print("Simulation time:", traci.simulation.getTime())
    print("Active vehicles at end:", remaining_vehicles)
    print("Vehicles waiting to enter:", pending_vehicles)
    print("Total unfinished vehicles:", unfinished_vehicles)

finally:
    traci.close()
