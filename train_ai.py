
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.metrics import confusion_matrix
from sklearn.dummy import DummyClassifier
import joblib

data = pd.read_csv("traffic_data.csv")

features = [
    "vehicle_count",
    "queue_length",
    "average_speed",
    "waiting_time"
]

lookahead = 10
congestion_threshold = 3

data["future_max_queue"] = (
    data["queue_length"]
    .rolling(lookahead, min_periods=lookahead)
    .max()
    .shift(-lookahead)
)

data["congestion"] = (
    data["future_max_queue"] >= congestion_threshold
).astype(int)

data = data.dropna().copy()

if len(data) < 30:
    print("Not enough data. Run a longer simulation.")
    raise SystemExit

if data["congestion"].nunique() < 2:
    print("The dataset contains only one congestion class.")
    print("We need more varied traffic scenarios to train this model.")
    raise SystemExit

X = data[features]
y = data["congestion"]

from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

if y_train.nunique() < 2 or y_test.nunique() < 2:
    print("The training or testing period lacks both classes.")
    print("Collect more varied traffic data before training.")
    raise SystemExit

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=6,
    random_state=42,
    class_weight="balanced"
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)

baseline = DummyClassifier(strategy="most_frequent")
baseline.fit(X_train, y_train)
baseline_predictions = baseline.predict(X_test)

print("\nAI MODEL RESULTS")
print("----------------")
print("Training observations:", len(X_train))
print("Testing observations:", len(X_test))
print("AI accuracy:", round(accuracy_score(y_test, predictions), 3))
print("Baseline accuracy:", round(
    accuracy_score(y_test, baseline_predictions), 3
))

print("\nConfusion matrix:")
print(confusion_matrix(y_test, predictions, labels=[0, 1]))

print("\nClassification report:")
print(classification_report(
    y_test,
    predictions,
    labels=[0, 1],
    target_names=["No congestion", "Congestion"],
    zero_division=0
))

importance = pd.Series(
    model.feature_importances_,
    index=features
).sort_values(ascending=False)

print("\nFeature importance:")
print(importance)

joblib.dump(model, "congestion_model.pkl")
print("\nModel saved as congestion_model.pkl")
