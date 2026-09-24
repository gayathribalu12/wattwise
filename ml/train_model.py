import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier

DATA_FILE = "data/raw/telemetry.csv"
MODEL_FILE = "ml/wattwise_model.pkl"

FEATURES = [
    "node_cpu_percent",
    "node_memory_percent",
    "container_cpu_percent",
    "container_memory_mb",
]


df = pd.read_csv(DATA_FILE)

X = df[FEATURES]
y = df["workload_type"]

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
)

model.fit(X, y)

joblib.dump(
    {
        "model": model,
        "features": FEATURES,
    },
    MODEL_FILE,
)

print("WATTWISE model trained successfully.")
print(f"Saved model to: {MODEL_FILE}")
print()
print("Classes:")
print(model.classes_)