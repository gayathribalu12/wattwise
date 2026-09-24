import time

print("WATTWISE memory workload started", flush=True)

blocks = []

while True:
    blocks.append(bytearray(100 * 1024 * 1024))

    print(
        f"Allocated approximately {len(blocks) * 100} MB",
        flush=True,
    )

    time.sleep(5)