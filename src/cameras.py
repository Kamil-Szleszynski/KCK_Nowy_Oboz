import cv2
import threading
import mediapipe as mp # używana wersja mediapipe 0.10.21
import numpy as np # używana do trygonometrii katów


class CameraStream:
    def __init__(self, src):
        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) #ustawienie bufora pamieci na 1 klatke w celu najswiezszego obrazu
        self.ret, self.frame = False, None #status i klatka
        self.started = False #flaga dzialania
        self.read_lock = threading.Lock()

    def start(self):
        self.started = True
        self.thread = threading.Thread(target=self.update, args=(), daemon=True) #watek na update flaga deamon automatycznie zamyka watek po zamknieciu programu
        self.thread.start()
        return self

    def update(self):
        while self.started: #tylko kiedy dziala
            ret, frame = self.cap.read() #czytanie klatki
            with self.read_lock: #blokada na zmienne
                self.ret, self.frame = ret, frame #podmiana aktualnej klatki

    def read(self):
        with self.read_lock:
            if self.frame is not None:
                return self.ret, cv2.resize(self.frame, (640, 480)) #zwraca status i przeskalowana klatke
            return self.ret, None

    def stop(self):
        self.started = False
        if hasattr(self, 'thread') and self.thread.is_alive(): # hasattr(self, 'thread') sparwdza czy obiekt ma atrybt thread, sprawdzamy czy watek dalej dziala
            self.thread.join(timeout=1.0)
        if self.cap.isOpened(): #sprawdzenie polaczenia z kamera
            self.cap.release() #odlaczenie kamery


class DeadliftAnalyzer:
    def __init__(self):
        self.stage = "standing" #stan cwiczenia
        self.feedback = "Ustaw sie do sztangi" #porady dla cwiczacego
        self.running = True
        self.feedback_lock = threading.Lock()
        self.front_error = False #flaga bledu przedniej kamery

        self.mp_pose = mp.solutions.pose #modul odpowiedzalny za wykrywanie ciala
        self.mp_drawing = mp.solutions.drawing_utils #narzedzia do rysowania na ekranie
        #zmienne odpowiedzalne za powtorzenia cwiczacego
        self.end = False
        self.repetitions = 0
        self.want_repetitions = 0
        self.rep_counted = False

        self.points = 100.0
        self.rep_scores = []
        #inicjalizacja sztucznej inteligencji min_detection_confidence sluzy aby AI bylo w 50% pewne ze widzi dany punkt
        # min_tracking_confidence sluzy aby AI sledzilo ruch gdy jest w 50% pewne
        self.pose_front = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.pose_side = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    def set_want_repetitions(self, a):
        self.want_repetitions = a
    #metoda do liczenia katow na zgieciach stawow
    def calculate_angle(self, a, b, c):
        a = np.array(a) #a to tablica [0] to wartosc x a [1] to wartosc y
        b = np.array(b) #uzywamy np.array do lepszych operacji matematycznych
        c = np.array(c)
        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        # Oblicza kąty dwóch wektorów (B->C oraz B->A) względem poziomu,
        # a następnie odejmuje je od siebie, dając wewnętrzny kąt zgięcia stawu w radianach
        angle = np.abs(radians * 180.0 / np.pi) #przeliczenie radianow na stopnie
        if angle > 180.0: #czlowiek maksymalnie moze zgiac np kolano o 180 stopni, chcemy kat wewnetrzy
            angle = 360 - angle
        return angle

    def analyze_front(self, landmarks):
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value] #pobranie koordynatow wybranych punktow
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        #oblicza pod jakim katem wzgledem ziemi ulozone sa barki i biodra
        angle_shoulders = np.abs(
            np.arctan2(left_shoulder.y - right_shoulder.y, left_shoulder.x - right_shoulder.x) * 180.0 / np.pi)
        angle_hips = np.abs(np.arctan2(left_hip.y - right_hip.y, left_hip.x - right_hip.x) * 180.0 / np.pi)
        #ujednolicenie wynikow o ile stopni o podloza odchylone sa barki i biodra
        dev_shoulders = np.abs(angle_shoulders - 180) if angle_shoulders > 90 else angle_shoulders
        dev_hips = np.abs(angle_hips - 180) if angle_hips > 90 else angle_hips

        with self.feedback_lock: #blokada na zmienna feedback, zeby tylko jeden watek na raz mogl ja zmienic
            if dev_shoulders > 12.0: #spawdzenie warunkow odchylenia z tolerancja(idealnie 0)
                self.feedback = "Krzywe barki! Wyrownaj chwyt."
                self.front_error = True #priorytet na blad z przedniej kamery
                self.points -= 0.10 #odejmowanie punktow poprawnosci
            elif dev_hips > 15.0:
                self.feedback = "Krzywe biodra! Pchaj rowno z obu nog."
                self.front_error = True
                self.points -= 0.10
            else:
                self.front_error = False

    def analyze_side(self, landmarks):
        left_shoulder = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, #value wyciaga indeks spod landmarks
                         landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        left_hip = [landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].x,
                    landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].y]
        left_knee = [landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                     landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        left_ankle = [landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                      landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

        right_hand = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        #obliczenie kata ugiecia kolana i biodra
        left_knee_angle = self.calculate_angle(left_hip, left_knee, left_ankle)
        left_hip_angle = self.calculate_angle(left_shoulder, left_hip, left_knee)

        with self.feedback_lock:
            if self.front_error: #jesli jest blad na przedniej kamerze to czeka az cwiczacy sie poprawi
                return

            if right_hand.y < (right_shoulder.y - 0.05): #awaryjne zakonczenie programu gdy uzytkownik podniesie reke
                self.end = True
            #Zmienne określające wzorcowe granice kątów dla konkretnych faz
            setup_knee_max = 155
            setup_hip_max = 125
            lockout_angle = 155
            lowering_angle = 145
            #faza stania gdy ugna sie kolana i biodra przechodzimy w faze gotowosci
            if self.stage == "standing":
                if left_knee_angle < setup_knee_max and left_hip_angle < setup_hip_max:
                    self.stage = "setup"
                    self.feedback = "Pozycja startowa OK. Ciagnij!"
                else:
                    self.feedback = "Ustaw sie do sztangi"
                return
            #Jeśli prostujesz nogi (>160), a plecy nadal leżą pochylone (<90), system krzyczy i ucina punkty.
            if self.stage == "setup" and left_knee_angle > 160 and left_hip_angle < 90:
                self.feedback = "Biodra za wysoko! Nie prostuj kolan za wczesnie."
                self.points -= 0.10
                return
            #Gdy kąty zaczynają rosnąć (wstajesz z poprawną pozycją), faza zmienia się na podnoszenie
            if self.stage == "setup" and (left_knee_angle > setup_knee_max + 5 or left_hip_angle > setup_hip_max + 5):
                self.stage = "lifting"
                self.feedback = "Wznoszenie. Trzymaj proste plecy!"
                return
            #Stawy są wyprostowane (>155°). Przechodzimy w fazę lockout (zatrzaśnięcie na górze)
            if self.stage == "lifting" and left_knee_angle > lockout_angle and left_hip_angle > lockout_angle:
                self.stage = "lockout"
                self.rep_counted = True #flaga ze podniosles sie od tej pory program bedzie naliczal powtorzenia
                self.feedback = "Pelny wyprost! Teraz odloz sztange."
                return
            #Kąty zaczynają maleć, odkładasz ciężar. Faza: opuszczanie
            if self.stage == "lockout" and (left_knee_angle < lowering_angle or left_hip_angle < lowering_angle):
                self.stage = "lowering"
                self.feedback = "Kontroluj opuszczanie ciezaru."
                return
            #Opadniecie w dol, reset faz naliczenie powtorzenia od nowa
            if self.stage == "lowering" and left_knee_angle < setup_knee_max and left_hip_angle < setup_hip_max:
                self.stage = "setup"
                if self.rep_counted:
                    self.repetitions += 1
                    self.rep_counted = False
                    self.rep_scores.append(self.points)
                    self.points = 100.0
                    #zakonczenie jesli mamy wyznaczana ilosc powtorzen
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
        cam_side = CameraStream("http://10.211.229.127:8080/video").start() #uruchomienie kamer

        print("Uruchomiono system dwukamerowy. Naciśnij 'q', aby zamknąć.")

        while True:
            ret_f, frame_f = cam_front.read()
            ret_s, frame_s = cam_side.read() #czytanie klatek

            if self.end: #flaga na wyjscie z petli
                break

            if not ret_f or not ret_s or frame_f is None or frame_s is None: #jesli nie udalo sie odczytac pojedynczej klatki pomijamy dana klatke
                continue

            frame_f_rgb = cv2.cvtColor(frame_f, cv2.COLOR_BGR2RGB) #mediapipe musi miec kolory w rgb wiec robimy konwersje
            results_f = self.pose_front.process(frame_f_rgb) #przetwarzanie modelu AI
            if results_f.pose_landmarks: #jesli AI znalazlo sylwetke rysuje szkielet i przekazuje punkty do analizy
                self.mp_drawing.draw_landmarks(frame_f, results_f.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
                self.analyze_front(results_f.pose_landmarks.landmark)

            frame_s_rgb = cv2.cvtColor(frame_s, cv2.COLOR_BGR2RGB) #to samo tylko kamera boczna
            results_s = self.pose_side.process(frame_s_rgb)
            if results_s.pose_landmarks:
                self.mp_drawing.draw_landmarks(frame_s, results_s.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
                self.analyze_side(results_s.pose_landmarks.landmark)
            cv2.putText(frame_f, f"Status: {self.feedback}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA) #nakladanie tekstu na obraz
            cv2.putText(frame_f, f"Reps: {self.repetitions}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(frame_f, f"Punkty: {int(self.points)}", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)

            combined = cv2.hconcat([frame_f, frame_s]) #laczenie widoku z 2 kamer
            cv2.imshow("ANALIZA MARTWEGO CIAGU: LEWA (FRONT) | PRAWA (BOK)", combined)

            if cv2.waitKey(1) & 0xFF == ord('q'): #awaryjne wyjscie gdy klikniesz q
                self.end = True
                break
        #wylaczenie programu i zamkniecie okien
        self.running = False
        cam_front.stop()
        cam_side.stop()
        self.pose_front.close()
        self.pose_side.close()
        cv2.destroyAllWindows()