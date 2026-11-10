
import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv("traffic_data.csv")

print("First five rows of traffic data:")
print(data.head())

print("\nSummary of traffic data:")
print(data.describe())

plt.figure(figsize=(10, 5))
plt.plot(data["time"], data["vehicle_count"])
plt.xlabel("Simulation Time (seconds)")
plt.ylabel("Number of Vehicles")
plt.title("Vehicle Count Over Time")
plt.grid(True)
plt.tight_layout()
plt.savefig("vehicle_count.png")
plt.show()

plt.figure(figsize=(10, 5))
plt.plot(data["time"], data["queue_length"])
plt.xlabel("Simulation Time (seconds)")
plt.ylabel("Stopped Vehicles")
plt.title("Traffic Queue Length Over Time")
plt.grid(True)
plt.tight_layout()
plt.savefig("queue_length.png")
plt.show()

plt.figure(figsize=(10, 5))
plt.plot(data["time"], data["average_speed"])
plt.xlabel("Simulation Time (seconds)")
plt.ylabel("Average Speed (m/s)")
plt.title("Average Traffic Speed Over Time")
plt.grid(True)
plt.tight_layout()
plt.savefig("average_speed.png")
plt.show()

print("\nAnalysis completed!")
print("Three graphs have been saved.")
