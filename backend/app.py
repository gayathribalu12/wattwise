import pandas as pd
import joblib
from pathlib import Path
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from .prometheus_client import get_node_metrics
from fastapi import FastAPI
from pydantic import BaseModel

from .optimizer import NodeState, optimize

MODEL_FEATURES = [
    "node_cpu_percent",
    "node_memory_percent",
    "container_cpu_percent",
    "container_memory_mb",
]


MODEL_FILE = Path("ml/wattwise_model.pkl")


def load_ml_model():

    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            "ML model not found. Run: python ml/train_model.py"
        )

    saved_model = joblib.load(MODEL_FILE)

    return saved_model["model"]


app = FastAPI(
    title="WATTWISE API",
    description="Virtual Data Center Energy Autopilot",
    version="0.1.0",
)


class NodeRequest(BaseModel):
    node_id: str
    cpu_percent: float
    memory_percent: float
    temperature_c: float


class OptimizationRequest(BaseModel):
    cpu_required: float
    memory_required: float
    nodes: list[NodeRequest]


@app.get("/")
def root():
    return {
        "name": "WATTWISE",
        "status": "online",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }

@app.get("/nodes")
def get_nodes():
    node = get_node_metrics()

    return {
        "nodes": [node]
    }

@app.post("/optimize-live")
def optimize_live_workload():

    # --------------------------------------------------------
    # Load telemetry
    # --------------------------------------------------------

    data_file = Path("data/raw/telemetry.csv")

    df = pd.read_csv(data_file)

    if df.empty:
        return {
            "status": "ERROR",
            "reason": "Telemetry dataset is empty.",
        }

    latest = df.iloc[-1]

    # --------------------------------------------------------
    # Load ML model
    # --------------------------------------------------------

    model = load_ml_model()

    prediction_input = pd.DataFrame(
        [
            {
                "node_cpu_percent": latest["node_cpu_percent"],
                "node_memory_percent": latest["node_memory_percent"],
                "container_cpu_percent": latest["container_cpu_percent"],
                "container_memory_mb": latest["container_memory_mb"],
            }
        ]
    )

    predicted_workload = model.predict(prediction_input)[0]

    probabilities = model.predict_proba(prediction_input)[0]

    confidence = max(probabilities)

    # --------------------------------------------------------
    # Convert workload prediction into resource requirement
    # --------------------------------------------------------

    if predicted_workload == "cpu_intensive":

        cpu_required = 15.0
        memory_required = 5.0

    elif predicted_workload == "memory_intensive":

        cpu_required = 5.0
        memory_required = 15.0

    else:

        return {
            "status": "ERROR",
            "reason": f"Unknown workload type: {predicted_workload}",
        }

    # --------------------------------------------------------
    # Current node
    # --------------------------------------------------------

    node = get_node_metrics()

    if (
        node["cpu_percent"] is None
        or node["memory_percent"] is None
    ):
        return {
            "status": "ERROR",
            "reason": "Live Prometheus metrics unavailable.",
        }

    # Temporary thermal placeholder.
    # This is NOT measured hardware temperature.
    temperature_c = 50.0

    live_node = NodeState(
        node_id=node["node_id"],
        cpu_percent=node["cpu_percent"],
        memory_percent=node["memory_percent"],
        temperature_c=temperature_c,
    )

    # --------------------------------------------------------
    # Run optimizer
    # --------------------------------------------------------

    result = optimize(
        nodes=[live_node],
        cpu_required=cpu_required,
        memory_required=memory_required,
    )

    # --------------------------------------------------------
    # Return complete decision
    # --------------------------------------------------------

    return {
        "status": "OK",
        "predicted_workload": predicted_workload,
        "confidence": round(float(confidence), 3),
        "resource_requirement": {
            "cpu_required": cpu_required,
            "memory_required": memory_required,
        },
        "node": node,
        "optimization": result,
    }

@app.post("/predict-workload")
def predict_workload():

    data_file = Path("data/raw/telemetry.csv")

    df = pd.read_csv(data_file)

    if df.empty:
        return {
            "status": "ERROR",
            "reason": "Telemetry dataset is empty.",
        }

    latest = df.iloc[-1]

    model = load_ml_model()

    prediction_input = pd.DataFrame(
        [
            {
                "node_cpu_percent": latest["node_cpu_percent"],
                "node_memory_percent": latest["node_memory_percent"],
                "container_cpu_percent": latest["container_cpu_percent"],
                "container_memory_mb": latest["container_memory_mb"],
            }
        ]
    )

    prediction = model.predict(prediction_input)[0]

    probabilities = model.predict_proba(prediction_input)[0]

    confidence = max(probabilities)

    return {
        "status": "OK",
        "predicted_workload": prediction,
        "confidence": round(float(confidence), 3),
        "telemetry": {
            "node_cpu_percent": latest["node_cpu_percent"],
            "node_memory_percent": latest["node_memory_percent"],
            "container_cpu_percent": latest["container_cpu_percent"],
            "container_memory_mb": latest["container_memory_mb"],
        },
    }