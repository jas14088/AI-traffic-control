
import xml.etree.ElementTree as ET
import statistics
import csv

EXPERIMENTS = {
    42: ("tripinfo_adaptive_600.xml", "tripinfo_fixed_600.xml"),
    123: ("tripinfo_adaptive_123.xml", "tripinfo_fixed_123.xml"),
    456: ("tripinfo_adaptive_456.xml", "tripinfo_fixed_456.xml"),
    789: ("tripinfo_adaptive_789.xml", "tripinfo_fixed_789.xml"),
    2026: ("tripinfo_adaptive_2026.xml", "tripinfo_fixed_2026.xml")
}

def analyze(file_name):
    root = ET.parse(file_name).getroot()
    trips = root.findall("tripinfo")

    durations = [float(t.get("duration", 0)) for t in trips]
    waiting = [float(t.get("waitingTime", 0)) for t in trips]
    time_loss = [float(t.get("timeLoss", 0)) for t in trips]

    return {
        "completed": len(trips),
        "duration": statistics.mean(durations) if durations else 0,
        "waiting": statistics.mean(waiting) if waiting else 0,
        "time_loss": statistics.mean(time_loss) if time_loss else 0,
        "total_waiting": sum(waiting)
    }

rows = []

for seed, (adaptive_file, fixed_file) in EXPERIMENTS.items():
    adaptive = analyze(adaptive_file)
    fixed = analyze(fixed_file)

    row = {
        "seed": seed,
        "adaptive_completed": adaptive["completed"],
        "fixed_completed": fixed["completed"],
        "adaptive_duration": adaptive["duration"],
        "fixed_duration": fixed["duration"],
        "adaptive_waiting": adaptive["waiting"],
        "fixed_waiting": fixed["waiting"],
        "adaptive_time_loss": adaptive["time_loss"],
        "fixed_time_loss": fixed["time_loss"],
        "adaptive_total_waiting": adaptive["total_waiting"],
        "fixed_total_waiting": fixed["total_waiting"]
    }

    rows.append(row)

    print(f"\nSeed {seed}")
    print(f"Completed trips: AI {adaptive['completed']} | Fixed {fixed['completed']}")
    print(f"Average duration: {adaptive['duration']:.2f} | {fixed['duration']:.2f} s")
    print(f"Average waiting: {adaptive['waiting']:.2f} | {fixed['waiting']:.2f} s")
    print(f"Average time loss: {adaptive['time_loss']:.2f} | {fixed['time_loss']:.2f} s")

metrics = [
    ("duration", "Average trip duration"),
    ("waiting", "Average waiting time"),
    ("time_loss", "Average time loss"),
    ("total_waiting", "Total waiting time")
]

print("\nFIVE-SEED AVERAGE COMPARISON")
print("-" * 65)

for metric, label in metrics:
    adaptive_values = [r[f"adaptive_{metric}"] for r in rows]
    fixed_values = [r[f"fixed_{metric}"] for r in rows]

    adaptive_avg = statistics.mean(adaptive_values)
    fixed_avg = statistics.mean(fixed_values)

    improvement = (
        (fixed_avg - adaptive_avg) / fixed_avg * 100
        if fixed_avg else 0
    )

    unit = "s"
    print(f"{label}:")
    print(f"  Adaptive AI: {adaptive_avg:.2f} {unit}")
    print(f"  Fixed-time:  {fixed_avg:.2f} {unit}")
    print(f"  Reduction:   {improvement:.2f}%")

with open("five_seed_results.csv", "w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("\nDetailed results saved to five_seed_results.csv")
