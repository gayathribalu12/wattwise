import requests


PROMETHEUS_URL = "http://localhost:9090"


def query_prometheus(query: str):
    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": query},
        timeout=5,
    )

    response.raise_for_status()

    data = response.json()

    if data["status"] != "success":
        raise RuntimeError("Prometheus query failed")

    results = data["data"]["result"]

    if not results:
        return None

    return float(results[0]["value"][1])


def get_node_metrics():
    cpu = query_prometheus(
        '100 * (1 - avg(rate(node_cpu_seconds_total{mode="idle"}[30s])))'
    )

    memory = query_prometheus(
        '100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)'
    )

    return {
        "node_id": "node-01",
        "cpu_percent": round(cpu, 2) if cpu is not None else None,
        "memory_percent": round(memory, 2) if memory is not None else None,
    }