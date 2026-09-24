import time
import requests
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

PROMETHEUS_URL = "http://localhost:9090"

OUTPUT_FILE = Path("data/raw/telemetry.csv")

QUERIES = {
    "cpu_usage": '100 * (1 - avg(rate(node_cpu_seconds_total{mode="idle"}[30s])))',
    "memory_usage": '100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)',
}


def query_prometheus(query):
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


def collect_sample():
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu_usage_percent": query_prometheus(QUERIES["cpu_usage"]),
        "memory_usage_percent": query_prometheus(QUERIES["memory_usage"]),
        "workload_type": "cpu_intensive",
    }


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    print("WATTWISE telemetry collector started")

    while True:
        try:
            sample = collect_sample()

            df = pd.DataFrame([sample])

            if OUTPUT_FILE.exists():
                df.to_csv(
                    OUTPUT_FILE,
                    mode="a",
                    header=False,
                    index=False,
                )
            else:
                df.to_csv(
                    OUTPUT_FILE,
                    index=False,
                )

            print(sample, flush=True)

        except Exception as error:
            print(f"Telemetry error: {error}", flush=True)

        time.sleep(5)


if __name__ == "__main__":
    main()
