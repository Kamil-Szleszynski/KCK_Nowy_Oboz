import cv2
import threading
import mediapipe as mp
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
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=1.0)

        if self.cap.isOpened():
            self.cap.release()


class DeadliftAnalyzer:
    def __init__(self):
        self.stage = "standing"
        self.feedback = "Ustaw sie do sztangi"
        self.running = True
        self.feedback_lock = threading.Lock()
        self.front_error = False

        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils

        self.end = False
        self.repetitions = 0
        self.want_repetitions = 0
        self.rep_counted = False

        self.points = 100.0
        self.rep_scores = []

        self.pose_front = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.pose_side = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    def set_want_repetitions(self, a):
        self.want_repetitions = a

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
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]

        angle_shoulders = np.abs(
            np.arctan2(left_shoulder.y - right_shoulder.y, left_shoulder.x - right_shoulder.x) * 180.0 / np.pi)
        angle_hips = np.abs(np.arctan2(left_hip.y - right_hip.y, left_hip.x - right_hip.x) * 180.0 / np.pi)

        dev_shoulders = np.abs(angle_shoulders - 180) if angle_shoulders > 90 else angle_shoulders
        dev_hips = np.abs(angle_hips - 180) if angle_hips > 90 else angle_hips

        with self.feedback_lock:
            if dev_shoulders > 12.0:
                self.feedback = "Krzywe barki! Wyrownaj chwyt."
                self.front_error = True
                self.points -= 0.10
            elif dev_hips > 15.0:
                self.feedback = "Krzywe biodra! Pchaj rowno z obu nog."
                self.front_error = True
                self.points -= 0.10
            else:
                self.front_error = False

    def analyze_side(self, landmarks):
        left_shoulder = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                         landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        left_hip = [landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].x,
                    landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].y]
        left_knee = [landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                     landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        left_ankle = [landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                      landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

        right_hand = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

        left_knee_angle = self.calculate_angle(left_hip, left_knee, left_ankle)
        left_hip_angle = self.calculate_angle(left_shoulder, left_hip, left_knee)

        with self.feedback_lock:
            if self.front_error:
                return

            if right_hand.y < (right_shoulder.y - 0.05):
                self.end = True

            setup_knee_max = 155
            setup_hip_max = 125
            lockout_angle = 155
            lowering_angle = 145

            if self.stage == "standing":
                if left_knee_angle < setup_knee_max and left_hip_angle < setup_hip_max:
                    self.stage = "setup"
                    self.feedback = "Pozycja startowa OK. Ciagnij!"
                else:
                    self.feedback = "Ustaw sie do sztangi"
                return

            if self.stage == "setup" and left_knee_angle > 160 and left_hip_angle < 90:
                self.feedback = "Biodra za wysoko! Nie prostuj kolan za wczesnie."
                self.points -= 0.10
                return

            if self.stage == "setup" and (left_knee_angle > setup_knee_max + 5 or left_hip_angle > setup_hip_max + 5):
                self.stage = "lifting"
                self.feedback = "Wznoszenie. Trzymaj proste plecy!"
                return

            if self.stage == "lifting" and left_knee_angle > lockout_angle and left_hip_angle > lockout_angle:
                self.stage = "lockout"
                self.rep_counted = True
                self.feedback = "Pelny wyprost! Teraz odloz sztange."
                return

            if self.stage == "lockout" and (left_knee_angle < lowering_angle or left_hip_angle < lowering_angle):
                self.stage = "lowering"
                self.feedback = "Kontroluj opuszczanie ciezaru."
                return

            if self.stage == "lowering" and left_knee_angle < setup_knee_max and left_hip_angle < setup_hip_max:
                self.stage = "setup"
                if self.rep_counted:
                    self.repetitions += 1
                    self.rep_counted = False
                    self.rep_scores.append(self.points)
                    self.points = 100.0

                    if self.want_repetitions > 0 and self.repetitions >= self.want_repetitions:
                        self.feedback = f"Koniec! Zrobiles {self.repetitions} powtorzen."
                        self.end = True
                        return

                    self.feedback = f"Zaliczone! Powtorzenie: {self.repetitions}"
                else:
                    self.feedback = "Pozycja startowa OK. Ciagnij!"

    def get_current_status(self):
        return self.feedback, self.stage, self.end, self.repetitions, self.points

    def main_loop(self):
        cam_front = CameraStream(0).start()
        cam_side = CameraStream("http://10.211.229.127:8080/video").start()

        print("Uruchomiono system dwukamerowy. Naciśnij 'q', aby zamknąć.")

        while True:
            ret_f, frame_f = cam_front.read()
            ret_s, frame_s = cam_side.read()

            if self.end:
                break

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
            cv2.putText(frame_f, f"Reps: {self.repetitions}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(frame_f, f"Punkty: {int(self.points)}", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)

            combined = cv2.hconcat([frame_f, frame_s])
            cv2.imshow("ANALIZA MARTWEGO CIAGU: LEWA (FRONT) | PRAWA (BOK)", combined)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.end = True
                break

        self.running = False
        cam_front.stop()
        cam_side.stop()
        self.pose_front.close()
        self.pose_side.close()
        cv2.destroyAllWindows()