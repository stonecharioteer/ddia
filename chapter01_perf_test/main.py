import time
import random
from fastapi import FastAPI

app = FastAPI()

def io_route():
    processing_delay = random.uniform(0.05, 0.15)
    time.sleep(processing_delay)

def cpu_route():
    result = 0
    for _ in range(10_000_000):
        result += 1

@app.get("/io")
def read_io():
    start_time = time.time()
    io_route()
    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000
    print(f"Request processed in {duration_ms:.2f} ms")
    return {"message": "Hello, DDIA!"}


@app.get("/cpu")
def read_cpu():
    start_time = time.time()
    cpu_route()
    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000
    print(f"Request processed in {duration_ms:.2f} ms")
    return {"message": "Hello, DDIA!"}
