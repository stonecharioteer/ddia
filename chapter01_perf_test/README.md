# Chapter 01: Performance Testing and Percentiles

This exercise is based on **Chapter 1** of *Designing Data-Intensive Applications* by Martin Kleppmann, focusing on understanding system performance through percentiles rather than simple averages.

## Overview

The chapter emphasizes that averages can be misleading when measuring system performance. A system might have an average response time of 200ms, but if the 99th percentile is 1.5 seconds, then 1 in 100 requests are experiencing poor performance. This matters because those slow requests often belong to customers who have the most data (and potentially the most value).

## What's Included

- `main.py`: FastAPI server with two endpoints demonstrating different performance characteristics
  - `/io`: Simulates I/O-bound operations with random delays (50-150ms)  
  - `/cpu`: Simulates CPU-bound operations with computational work
- `analyze.py`: Script to analyze server logs and calculate performance percentiles

## Running the Exercise

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Start the server:**
   ```bash
   # Single worker
   uv run uvicorn main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
   
   # Multiple workers for better performance testing
   uv run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 > server.log 2>&1 &
   ```

3. **Generate load using go-wrk:**
   ```bash
   # Test I/O endpoint with 10 concurrent connections for 5 minutes
   go-wrk -cpus 4 -c 10 -d 300 -T 15000 http://localhost:8000/io
   
   # Test CPU endpoint
   go-wrk -cpus 4 -c 10 -d 300 -T 15000 http://localhost:8000/cpu
   ```

4. **Analyze the results:**
   ```bash
   uv run python analyze.py server.log
   ```

## Key Learning Points

- **Percentiles matter more than averages** for understanding user experience
- **High percentiles** (p95, p99, p99.9) reveal the experience of your worst-affected users
- **Tail latencies** can significantly impact overall system performance
- **Response time measurements** should be taken from the client side when possible

## Expected Output

The analysis script will show metrics like:
```
--- Analysis of 1000 requests ---
Average latency: 99.87 ms
Median (p50):    99.45 ms
95th percentile: 148.23 ms
99th percentile: 149.85 ms
99.9th percentile: 149.98 ms
```

This demonstrates how different percentiles tell different stories about your system's performance.