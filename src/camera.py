import cv2
import mediapipe as mp #uzywana wersja mediapipe 0.10.21

class Camera:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        cv2.namedWindow("CyberTrener", cv2.WINDOW_NORMAL)
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.tolerance = 0.1
        self.pose = self.mp_pose.Pose()

    def open_camera(self):
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
            cv2.imshow("Analiza obrazu", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): #wyciecie 8 bitow zeby latwo sprawdzic kod klawisza
                break

camera = Camera()
camera.open_camera()