from msvcrt import locking

import cv2
import threading
import mediapipe as mp  # używana wersja mediapipe 0.10.21
import numpy as np
import time
from SpeechAssistant import speak


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
        self.stage = "standing"  # standing ,setup, lifting, lockout, lowering
        self.feedback = "Ustaw sie do sztangi"
        self.running = True
        self.feedback_lock = threading.Lock()
        self.front_error = False
        # Narzędzia MediaPipe
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.end = False

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
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]

        angle_shoulders = np.abs(np.arctan2(left_shoulder.y - right_shoulder.y, left_shoulder.x - right_shoulder.x) * 180.0 / np.pi)
        angle_hips = np.abs(np.arctan2(left_hip.y - right_hip.y, left_hip.x - right_hip.x) * 180.0 / np.pi)

        # Normalizujemy kąty, aby 0 oznaczało idealny poziom
        dev_shoulders = np.abs(angle_shoulders - 180) if angle_shoulders > 90 else angle_shoulders
        dev_hips = np.abs(angle_hips - 180) if angle_hips > 90 else angle_hips
        with self.feedback_lock:
            if  dev_shoulders > 5.0:
                self.feedback = "Krzywe barki! Wyrownaj chwyt."
                self.front_error = True
            elif dev_hips > 10.0:
                self.feedback = "Krzywe biodra! Pchaj rowno z obu nóg."
                self.front_error = True
            else:
                self.front_error = False
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
        right_hand = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_knee_angle = self.calculate_angle(left_hip, left_knee, left_ankle)
        left_hip_angle = self.calculate_angle(left_shoulder, left_hip, left_knee)

        with self.feedback_lock:
            if self.front_error:
                return
            if right_hand.y < (right_shoulder.y - 0.05):
                self.end = True
            # 1. CZŁOWIEK DOPIERO STOI (Stan początkowy przed ćwiczeniem)
            if self.stage == "standing":
                if left_knee_angle < 112 and left_hip_angle < 95:
                    self.stage = "setup"
                    self.feedback = "Pozycja startowa OK. Ciagnij!"
                else:
                    self.feedback = "Ustaw sie do sztangi"
                return

            # 2. FAZA STARTOWA (Gdy już ćwiczy i wraca na dół do kolejnego powtórzenia)
            if left_knee_angle < 112 and left_hip_angle < 95:
                self.stage = "setup"
                self.feedback = "Pozycja startowa OK. Ciagnij!"
                return

            # 3. BŁĄD: Biodra "strzelają" do góry (Tylko jeśli startuje z dołu)
            if self.stage == "setup" and left_knee_angle > 115 and left_hip_angle < 85:
                self.feedback = "Biodra za wysoko! Nie prostuj kolan za wczesnie."
                return

            # 4. FAZA WZNOSZENIA (Ruch z dołu w górę)
            if self.stage == "setup" and (left_knee_angle >= 112 or left_hip_angle >= 95):
                self.stage = "lifting"
                self.feedback = "Wznoszenie Trzymaj proste plecy!"
                return

            # 5. FAZA LOCKOUT (Pełny wyprost - dozwolony tylko, jeśli wcześniej podnosił)
            if self.stage == "lifting" and left_knee_angle > 165 and left_hip_angle > 165:
                self.stage = "lockout"
                self.feedback = "Pelny wyprost. Brawo!"
                return

            # 6. FAZA OPUSZCZANIA
            if self.stage == "lockout" and (left_knee_angle < 158 or left_hip_angle < 155):
                self.stage = "lowering"
                self.feedback = "Kontroluj opuszczanie ciężaru."
                return

            # 7. POWRÓT DO PODNOSZENIA (Gdyby po drodze w dół zatrzymał się i zaczął znowu ciągnąć)
            if self.stage == "lowering" and (left_knee_angle > 112 and left_knee_angle < 155):
                    # Opcjonalnie możesz tu zresetować do "setup" lub "lifting" przy odłożeniu ciężaru
                if left_knee_angle < 115 and left_hip_angle < 100:
                    self.stage = "setup"
    def report_feedback_loop(self):
        """Funkcja przeznaczona do działania w osobnym wątku - wypisuje status co 2 sekundy"""
        while self.running:
            print(f"[RAPORT SYSTEMU] Obecny status: {self.feedback} | Faza: {self.stage.upper()}")
            time.sleep(2.0)

    def get_current_status(self):
        """Zwraca aktualny feedback oraz fazę jako zmienne do wykorzystania poza klasą"""
        return self.feedback, self.stage, self.end
    def main_loop(self):
        cam_front = CameraStream(0).start()
        cam_side = CameraStream("http://10.165.247.219:8080/video").start()

        reporter_thread = threading.Thread(target=self.report_feedback_loop, daemon=True)
        reporter_thread.start()

        print("Uruchomiono system dwukamerowy z raportowaniem w tle. Naciśnij 'q', aby zamknąć.")

        while (True):
            ret_f, frame_f = cam_front.read()
            ret_s, frame_s = cam_side.read()
            if self.end == True:
                break;
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
        self.pose_front.close()
        self.pose_side.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    analyzer = DeadliftAnalyzer()
    watek_analizy = threading.Thread(target=analyzer.main_loop, daemon=True)
    watek_analizy.start()
    try:
        while True:
            time.sleep(1.0)  # pytamy co sekundę
            komunikat, faza, end = analyzer.get_current_status()
            print(f"[Zewnetrzny Odczyt] Komunikat: {komunikat} | Faza: {faza}")
            speak(komunikat)
            if end == True:
                break
    except KeyboardInterrupt:
        print("Zakończono odczyt zewnętrzny.")