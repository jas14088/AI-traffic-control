
import os
import sys
import subprocess
import xml.etree.ElementTree as ET
import pandas as pd
import re

SEEDS = [42, 43, 44, 45, 46]

TRAFFIC_FILE = "traffic.rou.xml"

EXPERIMENTS = [
    ("Fixed-time", "main.py"),
    ("Adaptive", "adaptive_controller.py")
]

all_results = []


def run_experiment(controller, script, seed):
    name = controller.lower().replace("-", "_")

    trip_file = f"heavy_tripinfo_{name}_{seed}.xml"
    csv_file = f"heavy_data_{name}_{seed}.csv"
    route_file = f"heavy_routes_{name}_{seed}.xml"
    log_file = f"heavy_log_{name}_{seed}.txt"

    env = os.environ.copy()
    env["SEED"] = str(seed)
    env["TRAFFIC_FILE"] = TRAFFIC_FILE
    env["TRIPINFO_FILE"] = trip_file
    env["OUTPUT_FILE"] = csv_file
    env["ROUTE_FILE"] = route_file

    print(f"\nRunning {controller}, seed {seed}...")
    print(f"Traffic input: {TRAFFIC_FILE}")

    try:
        process = subprocess.run(
            [sys.executable, script],
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as error:
        with open(log_file, "w", encoding="utf-8") as log:
            log.write(error.stdout or "")
            log.write(error.stderr or "")

        print(f"\nERROR: {controller}, seed {seed} failed.")
        print(f"Check the log file: {log_file}")
        print(error.stderr or error.stdout or "No error details available.")
        raise

    with open(log_file, "w", encoding="utf-8") as log:
        log.write(process.stdout or "")
        log.write(process.stderr or "")

    print(process.stdout)

    active_match = re.search(
        r"Active vehicles at end:\s*(\d+)",
        process.stdout
    )
    pending_match = re.search(
        r"Vehicles waiting to enter:\s*(\d+)",
        process.stdout
    )

    if not active_match or not pending_match:
        raise ValueError(
            f"Could not read final vehicle counts for {controller}, "
            f"seed {seed}. Check {log_file}."
        )

    active_vehicles = int(active_match.group(1))
    pending_vehicles = int(pending_match.group(1))
    unfinished_vehicles = active_vehicles + pending_vehicles

    if not os.path.exists(trip_file):
        raise FileNotFoundError(
            f"Trip information file was not created: {trip_file}"
        )

    root = ET.parse(trip_file).getroot()
    trips = []

    for trip in root.findall("tripinfo"):
        trips.append({
            "duration": float(trip.get("duration", 0)),
            "waiting_time": float(trip.get("waitingTime", 0)),
            "time_loss": float(trip.get("timeLoss", 0))
        })

    completed_trips = len(trips)

    print("Completed trips:", completed_trips)
    print("Active vehicles at end:", active_vehicles)
    print("Vehicles waiting to enter:", pending_vehicles)
    print("Total unfinished vehicles:", unfinished_vehicles)

    if not trips:
        print(
            f"Warning: no completed trips for {controller}, seed {seed}"
        )

        return {
            "traffic_scenario": "Heavy",
            "controller": controller,
            "seed": seed,
            "completed_trips": 0,
            "active_vehicles": active_vehicles,
            "pending_vehicles": pending_vehicles,
            "unfinished_vehicles": unfinished_vehicles,
            "average_duration": float("nan"),
            "average_waiting_time": float("nan"),
            "average_time_loss": float("nan")
        }

    df = pd.DataFrame(trips)

    result = {
        "traffic_scenario": "Heavy",
        "controller": controller,
        "seed": seed,
        "completed_trips": completed_trips,
        "active_vehicles": active_vehicles,
        "pending_vehicles": pending_vehicles,
        "unfinished_vehicles": unfinished_vehicles,
        "average_duration": df["duration"].mean(),
        "average_waiting_time": df["waiting_time"].mean(),
        "average_time_loss": df["time_loss"].mean()
    }

    print(
        f"Completed trips: {completed_trips} | "
        f"Average duration: {result['average_duration']:.2f}s | "
        f"Average waiting: {result['average_waiting_time']:.2f}s | "
        f"Average time loss: {result['average_time_loss']:.2f}s"
    )

    return result


for seed in SEEDS:
    for controller, script in EXPERIMENTS:
        result = run_experiment(controller, script, seed)
        all_results.append(result)

results = pd.DataFrame(all_results)
results.to_csv("heavy_repeated_experiment_results.csv", index=False)

valid = results.dropna(
    subset=[
        "average_duration",
        "average_waiting_time",
        "average_time_loss"
    ]
)

summary = valid.groupby("controller").agg(
    runs=("seed", "count"),
    mean_completed_trips=("completed_trips", "mean"),
    mean_active_vehicles=("active_vehicles", "mean"),
    mean_pending_vehicles=("pending_vehicles", "mean"),
    mean_unfinished_vehicles=("unfinished_vehicles", "mean"),
    mean_duration=("average_duration", "mean"),
    mean_waiting_time=("average_waiting_time", "mean"),
    mean_time_loss=("average_time_loss", "mean"),
    waiting_time_std=("average_waiting_time", "std")
).round(2)

summary.to_csv("heavy_repeated_experiment_summary.csv")

print("\nHEAVY-TRAFFIC REPEATED EXPERIMENT SUMMARY")
print("=" * 75)
print(summary.to_string())

if "Fixed-time" in summary.index and "Adaptive" in summary.index:
    fixed_wait = summary.loc["Fixed-time", "mean_waiting_time"]
    adaptive_wait = summary.loc["Adaptive", "mean_waiting_time"]

    if fixed_wait > 0:
        change = (adaptive_wait - fixed_wait) / fixed_wait * 100

        print(f"\nMean waiting-time change: {change:+.2f}%")

        if change < 0:
            print("Adaptive control recorded lower average waiting time.")
        elif change > 0:
            print("Adaptive control recorded higher average waiting time.")
        else:
            print("Both controllers recorded equal average waiting time.")

    fixed_duration = summary.loc["Fixed-time", "mean_duration"]
    adaptive_duration = summary.loc["Adaptive", "mean_duration"]

    if fixed_duration > 0:
        duration_change = (
            (adaptive_duration - fixed_duration) / fixed_duration
        ) * 100

        print(f"Mean trip-duration change: {duration_change:+.2f}%")

    fixed_loss = summary.loc["Fixed-time", "mean_time_loss"]
    adaptive_loss = summary.loc["Adaptive", "mean_time_loss"]

    if fixed_loss > 0:
        loss_change = (
            (adaptive_loss - fixed_loss) / fixed_loss
        ) * 100

        print(f"Mean time-loss change: {loss_change:+.2f}%")

print("\nHeavy-traffic experiment results saved.")
print("Detailed results: heavy_repeated_experiment_results.csv")
print("Summary results: heavy_repeated_experiment_summary.csv")
