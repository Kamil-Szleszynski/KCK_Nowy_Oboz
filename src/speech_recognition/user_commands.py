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
