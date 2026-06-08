import cv2
import threading
import mediapipe as mp  # używana wersja mediapipe 0.10.21
import numpy as np
import time


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

class DeadliftAnalyzer:
    def __init__(self):
        self.stage = "setup"  # setup, lifting, lockout, lowering
        self.feedback = "Ustaw sie do sztangi"
        self.running = True

        # Narzędzia MediaPipe
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils

        # Dwa osobne modele dla dwóch perspektyw
        self.pose_front = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.pose_side = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    def calculate_angle(self, a, b, c):
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        if angle > 180.0:
            angle = 360 - angle
        return angle

    def analyze_front(self, landmarks):
        """Analiza z przodu (Laptop): Sprawdzanie czy barki i biodra są równo (symetria)"""
        left_shoulder_y = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y
        right_shoulder_y = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y

        if abs(left_shoulder_y - right_shoulder_y) > 0.05:
            self.feedback = "Krzywe barki! Wyrownaj chwyt."

    def analyze_side(self, landmarks):
        """Analiza z boku (Telefon): Główna mechanika martwego ciągu"""
        left_shoulder = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                         landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        left_hip = [landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].x,
                    landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].y]
        left_knee = [landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                     landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        left_ankle = [landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                      landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

        left_knee_angle = self.calculate_angle(left_hip, left_knee, left_ankle)
        left_hip_angle = self.calculate_angle(left_shoulder, left_hip, left_knee)

        if left_knee_angle < 100 and left_hip_angle < 90:
            self.stage = "setup"
            self.feedback = "Pozycja startowa OK. Ciagnij!"

        if self.stage == "setup" and left_hip_angle > 120 and left_knee_angle < 120:
            self.feedback = "Biodra za wysoko! Obniz miednice."

        if left_knee_angle > 160 and left_hip_angle > 160:
            if self.stage != "lockout":
                self.feedback = "Pelny wyprost. Brawo!"
                self.stage = "lockout"
        elif left_knee_angle < 140:
            if self.stage == "lockout":
                self.stage = "lowering"
                self.feedback = "Kontroluj opuszczanie"

    def report_feedback_loop(self):
        """Funkcja przeznaczona do działania w osobnym wątku - wypisuje status co 2 sekundy"""
        while self.running:
            print(f"[RAPORT SYSTEMU] Obecny status: {self.feedback} | Faza: {self.stage.upper()}")
            time.sleep(2.0)

    def get_current_status(self):
        """Zwraca aktualny feedback oraz fazę jako zmienne do wykorzystania poza klasą"""
        return self.feedback, self.stage
    def main_loop(self):
        cam_front = CameraStream(0).start()
        cam_side = CameraStream("http://10.165.247.219:8080/video").start()

        reporter_thread = threading.Thread(target=self.report_feedback_loop, daemon=True)
        reporter_thread.start()

        print("Uruchomiono system dwukamerowy z raportowaniem w tle. Naciśnij 'q', aby zamknąć.")

        while True:
            ret_f, frame_f = cam_front.read()
            ret_s, frame_s = cam_side.read()

            if not ret_f or not ret_s or frame_f is None or frame_s is None:
                continue

            frame_f_rgb = cv2.cvtColor(frame_f, cv2.COLOR_BGR2RGB)
            results_f = self.pose_front.process(frame_f_rgb)
            if results_f.pose_landmarks:
                self.mp_drawing.draw_landmarks(frame_f, results_f.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
                self.analyze_front(results_f.pose_landmarks.landmark)

            frame_s_rgb = cv2.cvtColor(frame_s, cv2.COLOR_BGR2RGB)
            results_s = self.pose_side.process(frame_s_rgb)
            if results_s.pose_landmarks:
                self.mp_drawing.draw_landmarks(frame_s, results_s.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
                self.analyze_side(results_s.pose_landmarks.landmark)

            cv2.putText(frame_f, f"Status: {self.feedback}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)

            combined = cv2.hconcat([frame_f, frame_s])
            cv2.imshow("ANALIZA MATWREGO CIAGU: LEWA (FRONT) | PRAWA (BOK)", combined)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        self.running = False
        cam_front.stop()
        cam_side.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    analyzer = DeadliftAnalyzer()
    watek_analizy = threading.Thread(target=analyzer.main_loop, daemon=True)
    watek_analizy.start()
    try:
        while True:
            time.sleep(1.0)  # pytamy co sekundę
            komunikat, faza = analyzer.get_current_status()
            print(f"[Zewnetrzny Odczyt] Komunikat: {komunikat} | Faza: {faza}")
    except KeyboardInterrupt:
        print("Zakończono odczyt zewnętrzny.")