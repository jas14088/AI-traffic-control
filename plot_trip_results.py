
import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv("trip_level_summary.csv", index_col=0)

metrics = {
    "average_duration": (
        "Average Trip Duration",
        "Time (seconds)",
        "trip_duration_comparison.png"
    ),
    "average_waiting_time": (
        "Average Waiting Time",
        "Time (seconds)",
        "waiting_time_comparison.png"
    ),
    "average_time_loss": (
        "Average Time Loss",
        "Time (seconds)",
        "time_loss_comparison.png"
    )
}

for metric, details in metrics.items():
    title, ylabel, filename = details

    values = [
        data.loc["Fixed-time", metric],
        data.loc["Adaptive", metric]
    ]

    plt.figure(figsize=(7, 5))
    bars = plt.bar(
        ["Fixed-time", "AI Adaptive"],
        values
    )

    plt.title(title)
    plt.ylabel(ylabel)
    plt.grid(axis="y", linestyle="--", alpha=0.4)

    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:.2f}",
            ha="center",
            va="bottom"
        )

    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.show()
    plt.close()

print("All comparison graphs saved successfully!")
