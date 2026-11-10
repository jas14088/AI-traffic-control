
import csv
import traci
import os

CONFIG_FILE = "intersection.sumocfg"
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "traffic_data.csv")
END_TIME = 600

SEED = os.environ.get("SEED", "42")
TRIPINFO_FILE = os.environ.get(
    "TRIPINFO_FILE", "tripinfo_fixed.xml"
)
ROUTE_FILE = os.environ.get("ROUTE_FILE", "routes.xml")
TRAFFIC_FILE = os.environ.get("TRAFFIC_FILE", "traffic.rou.xml")

traci.start([
    "sumo",
    "-c", CONFIG_FILE,
    "-r", TRAFFIC_FILE,
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
            "waiting_time"
        ])

        while traci.simulation.getTime() < END_TIME:
            traci.simulationStep()

            time = traci.simulation.getTime()
            vehicles = traci.vehicle.getIDList()

            lanes = [
                lane for lane in traci.lane.getIDList()
                if not lane.startswith(":")
            ]

            vehicle_count = len(vehicles)

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

            writer.writerow([
                time,
                vehicle_count,
                queue_length,
                round(average_speed, 2),
                round(waiting_time, 2)
            ])

    remaining_vehicles = traci.vehicle.getIDCount()
    pending_vehicles = len(traci.simulation.getPendingVehicles())
    unfinished_vehicles = remaining_vehicles + pending_vehicles

    print("\nFixed-time simulation completed successfully!")
    print("Traffic data saved to", OUTPUT_FILE)
    print("Simulation time:", traci.simulation.getTime())
    print("Active vehicles at end:", remaining_vehicles)
    print("Vehicles waiting to enter:", pending_vehicles)
    print("Total unfinished vehicles:", unfinished_vehicles)

finally:
    traci.close()
