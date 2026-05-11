import cv2
import threading

class CameraStream:
    def __init__(self, src):
        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.ret, self.frame = False, None
        self.started = False
        self.read_lock = threading.Lock()

    def start(self):
        self.started = True
        self.thread = threading.Thread(target=self.update, args=(), daemon=True)
        self.thread.start()
        return self

    def update(self):
        while self.started:
            ret, frame = self.cap.read()
            with self.read_lock:
                self.ret, self.frame = ret, frame

    def read(self):
        with self.read_lock:
            if self.frame is not None:
                return self.ret, cv2.resize(self.frame, (640, 480))
            return self.ret, None

    def stop(self):
        self.started = False
        self.cap.release()

cam_front = CameraStream(0).start()

cam_side = CameraStream(f"http://10.181.151.153:8080/video").start()

print("Uruchomiono podgląd z dwóch kamer. Naciśnij 'q', aby zamknąć.")

while True:
    ret_f, frame_f = cam_front.read()
    ret_s, frame_s = cam_side.read()

    if not ret_f or not ret_s or frame_f is None or frame_s is None:
        continue

    combined = cv2.hconcat([frame_f, frame_s])

    cv2.imshow("TEST POLACZENIA: LEWA (LAPTOP) | PRAWA (TELEFON)", combined)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam_front.stop()
cam_side.stop()
cv2.destroyAllWindows()