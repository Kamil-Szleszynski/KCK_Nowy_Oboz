# import pyttsx3
# import wave
# import os
#
# class SpeechSynthesizer:
#     def __init__(self, rate=150, volume=1.0):
#         # Inicjalizacja silnika pyttsx3
#         self.engine = pyttsx3.init()
#         self.engine.setProperty('rate', rate)  # Szybkość mowy
#         self.engine.setProperty('volume', volume)  # Głośność (0.0 do 1.0)
#
#     def speak_direct(self, text):
#         self.engine.say(text)
#         self.engine.runAndWait()
