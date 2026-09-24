from dataclasses import dataclass


@dataclass
class NodeState:
    node_id: str
    cpu_percent: float
    memory_percent: float
    temperature_c: float


def optimize(nodes: list[NodeState], cpu_required: float, memory_required: float):
    feasible_nodes = [
        node
        for node in nodes
        if node.cpu_percent + cpu_required <= 90
        and node.memory_percent + memory_required <= 90
        and node.temperature_c < 80
    ]

    if not feasible_nodes:
        return {
            "status": "NO_FEASIBLE_NODE",
            "selected_node": None,
            "reason": "No node satisfies CPU, memory and thermal constraints.",
        }

    # Initial baseline decision.
    # Later this score will use the ML energy prediction.
    selected = min(
        feasible_nodes,
        key=lambda node: (
            node.temperature_c,
            node.cpu_percent,
            node.memory_percent,
        ),
    )

    return {
        "status": "PLACED",
        "selected_node": selected.node_id,
        "reason": (
            "Selected the feasible node with the lowest "
            "thermal/resource score."
        ),
    }
