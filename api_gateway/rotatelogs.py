import os
import time
import socket

LOG_FILE = "logs/internal"
MAX_FILE_SIZE = 10*1024*1024
TCP_HOST = "aggregator.bykea.prod"
TCP_PORT = 7799
DWELL_TIME = 100
while True:
    try:
        if os.path.getsize(LOG_FILE) > MAX_FILE_SIZE:
            with open(LOG_FILE, "r+") as f:
                logs = f.read()
                f.truncate(0)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((TCP_HOST, TCP_PORT))
                s.sendall(logs.encode())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        time.sleep(DWELL_TIME)