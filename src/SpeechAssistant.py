import pyttsx3

def speak(audio):
    engine = pyttsx3.init() #uruchomienie silnika mowy
    voices = engine.getProperty('voices') #pobranie listy wszystkich lektorow
    engine.setProperty('voice', voices[0].id) #ustawienie konkretnego glosu do czytania
    engine.say(audio) #wyslanie komunikatu
    engine.runAndWait() #powiedznie na glos komunikatu

