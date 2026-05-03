import speech_recognition as sr

class VoiceCommandCenter:
    def __init__(self, language="en-US"):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.language = language
        self.is_running = True

        self.commands = {
            "hello": self.greet,
            "stop": self.shutdown
        }

    def greet(self):
        print(">> Assistant: Hello there! How can I help you today?")

    def shutdown(self):
        print(">> Assistant: Shutting down. Goodbye!")
        self.is_running = False

    def listen(self):
        with self.microphone as source:
            print("\n--- Listening... ---")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = self.recognizer.listen(source)

        try:
            raw_text = self.recognizer.recognize_google(audio, language=self.language)
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
        while self.is_running:
            command_text = self.listen()
            if command_text:
                self.process_command(command_text)

assistant = VoiceCommandCenter()
assistant.run()