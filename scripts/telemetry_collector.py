import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


# ============================================================
# WATTWISE TELEMETRY COLLECTOR
# ============================================================

PROMETHEUS_URL = "http://localhost:9090"
OUTPUT_FILE = Path("data/raw/telemetry.csv")

COLLECTION_INTERVAL_SECONDS = 5


# ============================================================
# PROMETHEUS QUERIES
# ============================================================

NODE_CPU_QUERY = """
100 * (
    1 - avg(rate(node_cpu_seconds_total{mode="idle"}[30s]))
)
"""

NODE_MEMORY_QUERY = """
100 * (
    1 - node_memory_MemAvailable_bytes
    / node_memory_MemTotal_bytes
)
"""


# ============================================================
# PROMETHEUS HELPER
# ============================================================

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


# ============================================================
# DOCKER CONTAINER ID
# ============================================================

def get_container_id(container_name: str):
    """
    Get the current Docker container ID.

    We use the Docker CLI instead of Docker TCP port 2375.
    This works with the current Docker Desktop + WSL setup.
    """

    result = subprocess.run(
        [
            "docker",
            "inspect",
            "-f",
            "{{.Id}}",
            container_name,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Could not find container '{container_name}': "
            f"{result.stderr.strip()}"
        )

    container_id = result.stdout.strip()

    if not container_id:
        raise RuntimeError(
            f"Docker returned an empty ID for '{container_name}'"
        )

    return container_id


# ============================================================
# CONTAINER TELEMETRY
# ============================================================

def get_container_metrics(container_name: str):
    """
    Get CPU and memory metrics for a specific Docker container.

    cAdvisor exposes metrics using:

        /docker/<container_id>

    CPU:
        rate(container_cpu_usage_seconds_total[30s])

    Memory:
        container_memory_working_set_bytes
    """

    container_id = get_container_id(container_name)

    # --------------------------------------------------------
    # Container CPU %
    # --------------------------------------------------------
    cpu_query = (
        "100 * rate("
        "container_cpu_usage_seconds_total"
        f'{{id="/docker/{container_id}",cpu="total"}}'
        "[30s])"
    )

    # --------------------------------------------------------
    # Container memory
    # --------------------------------------------------------
    memory_query = (
        "container_memory_working_set_bytes"
        f'{{id="/docker/{container_id}"}}'
    )

    container_cpu_percent = query_prometheus(cpu_query)

    memory_bytes = query_prometheus(memory_query)

    if memory_bytes is not None:
        container_memory_mb = memory_bytes / (1024 * 1024)
    else:
        container_memory_mb = None

    return container_cpu_percent, container_memory_mb


# ============================================================
# COLLECT ONE SAMPLE
# ============================================================

def collect_sample(workload_type: str, container_name: str):

    # Node-level telemetry
    node_cpu = query_prometheus(NODE_CPU_QUERY)

    node_memory = query_prometheus(NODE_MEMORY_QUERY)

    # Container-level telemetry
    container_cpu_percent, container_memory_mb = (
        get_container_metrics(container_name)
    )

    sample = {
        "timestamp": datetime.now(timezone.utc).isoformat(),

        "node_id": "node-01",

        "workload_type": workload_type,

        "container_name": container_name,

        "node_cpu_percent": (
            round(node_cpu, 2)
            if node_cpu is not None
            else None
        ),

        "node_memory_percent": (
            round(node_memory, 2)
            if node_memory is not None
            else None
        ),

        "container_cpu_percent": (
            round(container_cpu_percent, 2)
            if container_cpu_percent is not None
            else None
        ),

        "container_memory_mb": (
            round(container_memory_mb, 2)
            if container_memory_mb is not None
            else None
        ),
    }

    return sample


# ============================================================
# SAVE SAMPLE
# ============================================================

def save_sample(sample):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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


# ============================================================
# SELECT WORKLOAD
# ============================================================

def select_workload():

    print()
    print("=" * 60)
    print("WATTWISE TELEMETRY COLLECTOR")
    print("=" * 60)

    print()
    print("Available workloads:")
    print()
    print("1. CPU intensive")
    print("   Container: wattwise-cpu-worker")
    print()
    print("2. Memory intensive")
    print("   Container: wattwise-memory-worker")
    print()

    choice = input("Select workload type (1/2): ").strip()

    if choice == "1":

        workload_type = "cpu_intensive"

        container_name = "wattwise-cpu-worker"

    elif choice == "2":

        workload_type = "memory_intensive"

        container_name = "wattwise-memory-worker"

    else:

        raise ValueError(
            "Invalid choice. Please select 1 or 2."
        )

    return workload_type, container_name


# ============================================================
# MAIN
# ============================================================

def main():

    workload_type, container_name = select_workload()

    print()
    print("-" * 60)
    print(f"Workload type : {workload_type}")
    print(f"Container     : {container_name}")
    print(f"Output file   : {OUTPUT_FILE}")
    print(f"Interval      : {COLLECTION_INTERVAL_SECONDS} seconds")
    print("-" * 60)

    # --------------------------------------------------------
    # Verify Docker container
    # --------------------------------------------------------

    try:

        container_id = get_container_id(container_name)

        print()
        print("Docker container found:")
        print(container_id)

    except Exception as error:

        print()
        print(f"ERROR: {error}")

        return

    # --------------------------------------------------------
    # Start collection
    # --------------------------------------------------------

    print()
    print("Starting telemetry collection...")
    print("Press Ctrl+C to stop.")
    print()

    while True:

        try:

            sample = collect_sample(
                workload_type,
                container_name,
            )

            save_sample(sample)

            print(
                f"[{sample['timestamp']}] "
                f"node_cpu={sample['node_cpu_percent']}% | "
                f"node_mem={sample['node_memory_percent']}% | "
                f"container_cpu={sample['container_cpu_percent']}% | "
                f"container_mem={sample['container_memory_mb']} MB"
            )

        except KeyboardInterrupt:

            print()
            print("Telemetry collection stopped.")

            break

        except Exception as error:

            print(
                f"Telemetry error: {error}",
                flush=True,
            )

        time.sleep(COLLECTION_INTERVAL_SECONDS)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()