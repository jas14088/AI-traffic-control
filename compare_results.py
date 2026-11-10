
import xml.etree.ElementTree as ET
import statistics

FILES = {
    "Adaptive AI": "tripinfo_adaptive_123.xml",
    "Fixed-time": "tripinfo_fixed_123.xml"
}

def analyze(file_name):
    root = ET.parse(file_name).getroot()
    trips = root.findall("tripinfo")

    durations = [float(t.get("duration", 0)) for t in trips]
    waiting = [float(t.get("waitingTime", 0)) for t in trips]
    time_loss = [float(t.get("timeLoss", 0)) for t in trips]

    return {
        "completed": len(trips),
        "avg_duration": statistics.mean(durations) if durations else 0,
        "avg_waiting": statistics.mean(waiting) if waiting else 0,
        "avg_time_loss": statistics.mean(time_loss) if time_loss else 0,
        "total_waiting": sum(waiting)
    }

results = {
    name: analyze(file_name)
    for name, file_name in FILES.items()
}

print("\nTRAFFIC CONTROLLER COMPARISON")
print("-" * 72)

for name, data in results.items():
    print(f"\n{name}")
    print(f"Completed trips: {data['completed']}")
    print(f"Average duration: {data['avg_duration']:.2f} s")
    print(f"Average waiting: {data['avg_waiting']:.2f} s")
    print(f"Average time loss: {data['avg_time_loss']:.2f} s")
    print(f"Total waiting time: {data['total_waiting']:.2f} s")

print("\nADAPTIVE IMPROVEMENT")
for metric in ["avg_duration", "avg_waiting", "avg_time_loss"]:
    fixed = results["Fixed-time"][metric]
    adaptive = results["Adaptive AI"][metric]

    if fixed > 0:
        improvement = (fixed - adaptive) / fixed * 100
        print(f"{metric}: {improvement:.2f}%")

print("\nPositive percentages mean the adaptive controller reduced the metric.")
