import threading
import queue
import time
import speech_recognition as sr
import pyttsx3


class ThreadedVoiceAssistant:
    def __init__(self, language="en-US", rate=150, volume=1.0):
        self.language = language
        self.rate = rate
        self.volume = volume
        self.is_running = True

        # 1. Thread-safe queue for TTS text inputs
        self.speech_queue = queue.Queue()

        # 2. State flag to prevent the listener from hearing the assistant speak
        self.is_speaking = False

        self.commands = {
            "hello": self.greet,
            "stop": self.shutdown
        }

        # 3. Start the dedicated background thread for Speech
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()

    def _tts_worker(self):
        """
        Dedicated background worker for Text-to-Speech.
        Initializing pyttsx3 INSIDE this function ensures it stays on this thread.
        """
        engine = pyttsx3.init()
        engine.setProperty('rate', self.rate)
        engine.setProperty('volume', self.volume)

        while self.is_running:
            try:
                # Poll the queue with a timeout so it doesn't block shutdown indefinitely
                text = self.speech_queue.get(timeout=0.5)

                self.is_speaking = True  # Signal to the listener to hold off
                print(f">> Assistant (Speaking): {text}")

                engine.say(text)
                engine.runAndWait()  # Blocks only this background thread

                self.is_speaking = False  # Signal that it's safe to listen again
                self.speech_queue.task_done()
            except queue.Empty:
                continue

    def speak(self, text):
        """Non-blocking method to submit text to be spoken out loud."""
        self.speech_queue.put(text)

    def greet(self):
        self.speak("Hello there! How can I help you today?")

    def shutdown(self):
        self.speak("Shutting down. Goodbye!")
        # Wait for the speech queue to completely clear before stopping
        self.speech_queue.join()
        self.is_running = False

    def listen(self):
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()

        with microphone as source:
            # Loop/wait if the assistant happens to be finishing up a sentence
            while self.is_speaking:
                time.sleep(0.1)

            print("\n--- Listening... ---")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source)

        try:
            raw_text = recognizer.recognize_google(audio, language=self.language)
            return raw_text.lower()
        except sr.UnknownValueError:
            print("?? Error: Could not understand audio.")
        except sr.RequestError as e:
            print(f"?? Error: Could not request results; {e}")
        return ""

    def process_command(self, text):
        print(f"You said: {text}")

        for trigger, action in self.commands.items():
            if trigger in text:
                action()
                return

        print(".. No matching command found.")

    def run(self):
        print("Voice Assistant Activated.")
        # Wake up greeting
        self.speak("Voice assistant system online.")

        while self.is_running:
            # Double check we aren't speaking before entering blocking listen state
            if not self.is_speaking:
                command_text = self.listen()
                if command_text:
                    self.process_command(command_text)
            else:
                time.sleep(0.2)


if __name__ == "__main__":
    assistant = ThreadedVoiceAssistant()
    assistant.run()