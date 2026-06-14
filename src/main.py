import threading
import time
import queue
from gui import DeadliftApp
from cameras import DeadliftAnalyzer
from SpeechAssistant import speak
from DatabaseManager import DatabaseManager


class ApplicationController:
    def __init__(self):
        self.app = DeadliftApp(on_start_training=self.start_training) #inicalizacja klas przekazujemy ktora funkcje ma uruchomic przycisk zatwierdz
        self.analyzer = None
        self.db = DatabaseManager()

        self.speech_queue = queue.Queue() #kolejkowanie feedbacku
        self.tts_thread = threading.Thread(target=self.tts_engine_worker, daemon=True) #watek na komunikacje glosowa
        self.tts_thread.start()

    def tts_engine_worker(self):
        while True:
            text = self.speech_queue.get() #pobiera z kolejki tekst
            try:
                speak(text) #probuje mowic
            except Exception as e:
                print(f"Błąd TTS: {e}")
            finally:
                self.speech_queue.task_done() #usuwa tekst z kolejki

    def run(self):
        self.app.mainloop() #wlaczenie glownej aplikacji

    def start_training(self, sets, height, weight, reps): #metoda uruchamia sie po kliknineciu przycisku w gui
        print(f"Odebrano dane: Serie: {sets}, Powtorzenia: {reps}, Wzrost: {height}, Waga: {weight}")

        self.app.withdraw() #ukrywa gui
        self.app.update() #wymusza odswiezenie ekranu zeby gui na pewno zniknelo

        self.speech_queue.put("Zaczynamy trening. Ustaw się przy sztandze")
        time.sleep(5) #czas zeby cwiczacy mogl sie ustawic do cwiczenia

        for aktualna_seria in range(1, sets + 1): #petla dziala tyle razy ile jest serii
            print(f"\n--- ROZPOCZYNAMY SERIĘ {aktualna_seria} z {sets} ---")

            self.analyzer = DeadliftAnalyzer()
            self.analyzer.set_want_repetitions(reps) #przy kazdej serii AI sie resetuje

            monitoring_thread = threading.Thread(target=self.camera_monitor_worker, daemon=True) #watek na komunikacje glosowa
            monitoring_thread.start()

            self.analyzer.main_loop()
            time.sleep(0.5)

            if self.analyzer.rep_scores:
                self.db.save_session(self.analyzer.rep_scores) #zapisanie listy punktow do bazy danych

            if aktualna_seria < sets: #obsluga przerwy miedzy seriami
                self.speech_queue.put(f"Koniec serii {aktualna_seria}. Masz 5 sekund przerwy.")
                print(f"Przerwa... 5 sekund.")
                time.sleep(10)

        self.speech_queue.put("Koniec całego treningu. Świetna robota!") #poinformowanie o koncu treningu
        self.app.after(0, self.finish_training) #wykonienie funkcji finish_training/ pokaznie historii treningow

    def camera_monitor_worker(self):
        ostatni_komunikat = ""
        #obsluga komunikacji glosowej zmienna ostatni komunikat zapobiega ciaglemu powtarzeniu tego samego feedbacku
        while self.analyzer and self.analyzer.running:
            time.sleep(1.0)
            komunikat, faza, end, reps, points = self.analyzer.get_current_status()

            if komunikat != ostatni_komunikat:
                print(
                    f"[Zewnetrzny Odczyt] Komunikat: {komunikat} | Faza: {faza} | Reps: {reps} | Punkty: {int(points)}")
                self.speech_queue.put(komunikat)
                ostatni_komunikat = komunikat

            if end:
                break

    def finish_training(self):
        self.app.deiconify() #przywarca ukryte gui
        self.app.show_frame("TrainingHistory") #przeskakuje do okna historii treningow


if __name__ == "__main__":
    controller = ApplicationController()
    controller.run()