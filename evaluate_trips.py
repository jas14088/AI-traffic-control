
import xml.etree.ElementTree as ET
import pandas as pd

def read_tripinfo(filename, controller):
    tree = ET.parse(filename)
    root = tree.getroot()

    trips = []

    for trip in root.findall("tripinfo"):
        trips.append({
            "controller": controller,
            "vehicle_id": trip.get("id"),
            "duration": float(trip.get("duration", 0)),
            "waiting_time": float(trip.get("waitingTime", 0)),
            "time_loss": float(trip.get("timeLoss", 0)),
            "depart_delay": float(trip.get("departDelay", 0))
        })

    return trips

fixed = read_tripinfo("tripinfo_fixed.xml", "Fixed-time")
adaptive = read_tripinfo("tripinfo_adaptive.xml", "Adaptive")

df = pd.DataFrame(fixed + adaptive)

if df.empty:
    print("No completed vehicle trips found.")
    print("Check that both XML files contain tripinfo records.")
    raise SystemExit

summary = df.groupby("controller").agg(
    completed_trips=("vehicle_id", "count"),
    average_duration=("duration", "mean"),
    average_waiting_time=("waiting_time", "mean"),
    average_time_loss=("time_loss", "mean"),
    average_depart_delay=("depart_delay", "mean")
).round(2)

print("\nTRIP-LEVEL PERFORMANCE COMPARISON")
print("=" * 45)
print(summary.to_string())

metrics = [
    ("average_duration", "lower"),
    ("average_waiting_time", "lower"),
    ("average_time_loss", "lower")
]

print("\nADAPTIVE CONTROL CHANGE")
print("=" * 45)

for metric, direction in metrics:
    if "Fixed-time" not in summary.index or "Adaptive" not in summary.index:
        continue

    baseline = summary.loc["Fixed-time", metric]
    adaptive_value = summary.loc["Adaptive", metric]

    if baseline != 0:
        change = (adaptive_value - baseline) / baseline * 100
        print(f"{metric}: {change:+.2f}%")

df.to_csv("trip_level_results.csv", index=False)
summary.to_csv("trip_level_summary.csv")

print("\nSaved trip_level_results.csv")
print("Saved trip_level_summary.csv")
