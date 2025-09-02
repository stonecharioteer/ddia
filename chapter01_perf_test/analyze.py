import numpy as np
import sys

def analyze_logs(log_file):
    latencies = []
    with open(log_file, 'r') as f:
        for line in f:
            try:
                # Extracts the number from a line like "Request processed in 101.45 ms"
                latency_ms = float(line.split(' ')[3])
                latencies.append(latency_ms)
            except (IndexError, ValueError):
                # Ignore lines that aren't valid log entries
                continue

    if not latencies:
        print("No valid log entries found.")
        return

    # Use numpy to calculate the metrics
    p50 = np.percentile(latencies, 50)  # Median
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)
    p999 = np.percentile(latencies, 99.9)
    average = np.mean(latencies)

    print(f"--- Analysis of {len(latencies)} requests ---")
    print(f"Average latency: {average:.2f} ms")
    print(f"Median (p50):    {p50:.2f} ms")
    print(f"95th percentile: {p95:.2f} ms")
    print(f"99th percentile: {p99:.2f} ms")
    print(f"99.9th percentile: {p999:.2f} ms")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze.py <log_file>")
        sys.exit(1)
    analyze_logs(sys.argv[1])
