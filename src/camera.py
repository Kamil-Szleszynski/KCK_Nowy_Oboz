import cv2
import mediapipe as mp #uzywana wersja mediapipe 0.10.21
import numpy as np

class Camera:
    def __init__(self):
        self.stage = "setup"  # setup, lifting, lockout
        self.feedback = "Ustaw sie do sztangi"

    def calculate_angle(self, a, b, c):
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)

        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)

        if angle > 180.0:
            angle = 360 - angle

        return angle
    def dead_lift(self,landmarks):
        left_shoulder = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                    landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        left_hip = [landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].x,
               landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].y]
        left_knee = [landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        left_ankle = [landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                 landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
        right_shoulder = [landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                         landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
        right_hip = [landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                    landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value].y]
        right_knee = [landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE.value].x,
                     landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
        right_ankle = [landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value].x,
                      landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]
        left_knee_angle = self.calculate_angle(left_hip, left_knee, left_ankle) #kat kolana
        left_hip_angle = self.calculate_angle(left_shoulder, left_hip, left_knee) #kat biodra

        #stanie bokiem
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

        return self.feedback
        pass
    def open_camera(self):
        self.cap = cv2.VideoCapture(0)
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.tolerance = 0.1
        self.pose = self.mp_pose.Pose()
        while True:
            _, frame = self.cap.read()
            if not _:
                break
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(frame_rgb)
            if results.pose_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS
                )
            self.dead_lift(results.pose_landmarks.landmark)
            cv2.imshow("Analiza obrazu", frame)
            print(camera.feedback)
            if cv2.waitKey(1) & 0xFF == ord('q'): #wyciecie 8 bitow zeby latwo sprawdzic kod klawisza
                break

camera = Camera()
camera.open_camera()
