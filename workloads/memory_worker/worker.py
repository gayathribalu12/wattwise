import time

print("WATTWISE memory workload started", flush=True)

# Allocate approximately 500 MB and hold it.
memory_block = bytearray(500 * 1024 * 1024)

print("Allocated approximately 500 MB", flush=True)

while True:
    time.sleep(5)