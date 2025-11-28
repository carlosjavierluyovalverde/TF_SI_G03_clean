import cv2
import urllib.request
import numpy as np
import time

URL = "http://192.168.101.3:4747/video?640x480"
print("Iniciando test directo MJPEG...\n")

stream = urllib.request.urlopen(URL)
buffer = b""
last_time = time.time()
frames = 0

while True:
    buffer += stream.read(4096)

    start = buffer.find(b'\xff\xd8')
    end   = buffer.find(b'\xff\xd9')

    if start != -1 and end != -1:
        jpg = buffer[start:end+2]
        buffer = buffer[end+2:]

        frame = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            continue

        frames += 1
        now = time.time()
        if now - last_time >= 1:
            print(f"FPS directos reales: {frames}")
            frames = 0
            last_time = now

        cv2.imshow("MJPEG Directo", frame)
        if cv2.waitKey(1) == 27:
            break
