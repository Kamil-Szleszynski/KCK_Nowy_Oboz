import threading
import time
import queue
from gui import DeadliftApp
from cameras import DeadliftAnalyzer
from SpeechAssistant import speak
from DatabaseManager import DatabaseManager


class ApplicationController:
    def __init__(self):
        self.app = DeadliftApp(on_start_training=self.start_training)
        self.analyzer = None
        self.db = DatabaseManager()

        self.speech_queue = queue.Queue()
        self.tts_thread = threading.Thread(target=self.tts_engine_worker, daemon=True)
        self.tts_thread.start()

    def tts_engine_worker(self):
        while True:
            text = self.speech_queue.get()
            try:
                speak(text)
            except Exception as e:
                print(f"Błąd TTS: {e}")
            finally:
                self.speech_queue.task_done()

    def run(self):
        self.app.mainloop()

    def start_training(self, sets, height, weight, reps):
        print(f"Odebrano dane: Serie: {sets}, Powtorzenia: {reps}, Wzrost: {height}, Waga: {weight}")

        self.app.withdraw()
        self.app.update()

        self.speech_queue.put("Zaczynamy trening. Ustaw się przy sztandze")
        time.sleep(5)

        for aktualna_seria in range(1, sets + 1):
            print(f"\n--- ROZPOCZYNAMY SERIĘ {aktualna_seria} z {sets} ---")

            self.analyzer = DeadliftAnalyzer()
            self.analyzer.set_want_repetitions(reps)

            monitoring_thread = threading.Thread(target=self.camera_monitor_worker, daemon=True)
            monitoring_thread.start()

            self.analyzer.main_loop()
            time.sleep(0.5)

            if self.analyzer.rep_scores:
                self.db.save_session(self.analyzer.rep_scores)

            if aktualna_seria < sets:
                self.speech_queue.put(f"Koniec serii {aktualna_seria}. Masz 5 sekund przerwy.")
                print(f"Przerwa... 5 sekund.")
                time.sleep(10)

        self.speech_queue.put("Koniec całego treningu. Świetna robota!")
        self.app.after(0, self.finish_training)

    def camera_monitor_worker(self):
        ostatni_komunikat = ""

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
        self.app.deiconify()
        self.app.show_frame("TrainingHistory")


if __name__ == "__main__":
    controller = ApplicationController()
    controller.run()