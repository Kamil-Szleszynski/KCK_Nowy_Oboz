import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
cap = cv2.VideoCapture(".venv/ok.mp4")
pose = mp_pose.Pose()
tolerancja = 0.1
cv2.namedWindow("Analiza obrazu", cv2.WINDOW_NORMAL)
while True:
    _, frame = cap.read()
    if _ == False:
        print("Koniec filmu!")
        break
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(frame_rgb)
    landmarks = results.pose_landmarks.landmark
    if landmarks:
        ramie_lewe = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        ramie_prawe = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        nadgarstek_prawy = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
        nadgarstek_lewy = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
        T = [ramie_prawe.y,ramie_lewe.y,nadgarstek_prawy.y,nadgarstek_lewy.y]
        prosta_linia = max(T) - min(T)
        Legia_prawa = ramie_prawe.x-nadgarstek_prawy.x
        Legia_lewa = ramie_lewe.y-nadgarstek_lewy.y
        if abs(prosta_linia) < tolerancja:
            cv2.putText(frame, "T", (0, 200), cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 0, 0), 2)
        elif ramie_lewe.y>nadgarstek_lewy.y and ramie_prawe.y>nadgarstek_prawy.y:
            cv2.putText(frame, "Y", (0, 200), cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 0, 0), 2)
        elif nadgarstek_lewy.y > ramie_lewe.y and nadgarstek_prawy.y > ramie_prawe.y:
            cv2.putText(frame, "I", (0, 200), cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 0, 0), 2)
        elif ramie_prawe.y>nadgarstek_prawy.y and abs(Legia_prawa)<tolerancja and abs(Legia_lewa)<tolerancja:
            cv2.putText(frame, "L", (0, 200), cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 0, 0), 2)
        else:
            cv2.putText(frame, "?", (0, 200), cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 0, 0), 2)

        mp_drawing.draw_landmarks(frame,results.pose_landmarks,mp_pose.POSE_CONNECTIONS)
    else:
        print("Nie znaleziono czlowieka!")
        break
    cv2.imshow("Analiza obrazu", frame)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()