import time
import math

print("WATTWISE CPU workload started")

while True:
    start = time.time()

    # Controlled CPU computation
    while time.time() - start < 10:
        x = 0.0
        for i in range(1, 500000):
            x += math.sqrt(i) * math.sin(i)

    print("Completed workload batch")
    time.sleep(2)

