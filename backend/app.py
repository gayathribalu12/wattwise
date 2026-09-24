from .prometheus_client import get_node_metrics
from fastapi import FastAPI
from pydantic import BaseModel

from .optimizer import NodeState, optimize


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
def optimize_live_workload(
    cpu_required: float = 10,
    memory_required: float = 5,
):
    node = get_node_metrics()

    if node["cpu_percent"] is None or node["memory_percent"] is None:
        return {
            "status": "ERROR",
            "reason": "Live Prometheus metrics unavailable.",
        }

    live_node = NodeRequest(
        node_id=node["node_id"],
        cpu_percent=node["cpu_percent"],
        memory_percent=node["memory_percent"],
        temperature_c=50.0,
    )

    nodes = [
        NodeState(
            node_id=live_node.node_id,
            cpu_percent=live_node.cpu_percent,
            memory_percent=live_node.memory_percent,
            temperature_c=live_node.temperature_c,
        )
    ]

    return optimize(
        nodes=nodes,
        cpu_required=cpu_required,
        memory_required=memory_required,
    )


@app.post("/optimize")
def optimize_workload(request: OptimizationRequest):
    nodes = [
        NodeState(
            node_id=node.node_id,
            cpu_percent=node.cpu_percent,
            memory_percent=node.memory_percent,
            temperature_c=node.temperature_c,
        )
        for node in request.nodes
    ]

    return optimize(
        nodes=nodes,
        cpu_required=request.cpu_required,
        memory_required=request.memory_required,
    )
