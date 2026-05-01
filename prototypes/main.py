import pyttsx3
import speech_recognition as sr
import webbrowser
import datetime
import wikipedia
from translate import Translator

# this method is for taking the commands
# and recognizing the command from the
# speech_Recognition module we will use
# the recongizer method for recognizing
def takeCommand(lang='en-in'):
    r = sr.Recognizer()

    # from the speech_Recognition module
    # we will use the Microphone module
    # for listening the command
    with sr.Microphone() as source:
        print('Listening')

        # seconds of non-speaking audio before
        # a phrase is considered complete
        r.pause_threshold = 0.7
        audio = r.listen(source)

        # Now we will be using the try and catch
        # method so that if sound is recognized
        # it is good else we will have exception
        # handling
        try:
            print("Recognizing")

            # for Listening the command in indian
            # english we can also use 'hi-In'
            # for hindi recognizing
            Query = r.recognize_google(audio, language=lang)
            print("the command is printed=", Query)

        except Exception as e:
            print(e)
            print("Say that again sir")
            return "None"

        return Query


def speak(audio):
    engine = pyttsx3.init()
    # getter method(gets the current value
    # of engine property)
    voices = engine.getProperty('voices')

    # setter method .[0]=male voice and
    # [1]=female voice in set Property.
    engine.setProperty('voice', voices[0].id)

    # Method for the speaking of the assistant
    engine.say(audio)

    # Blocks while processing all the currently
    # queued commands
    engine.runAndWait()


def tellDay():
    # This function is for telling the
    # day of the week
    day = datetime.datetime.today().weekday() + 1

    # this line tells us about the number
    # that will help us in telling the day
    Day_dict = {1: 'Monday', 2: 'Tuesday',
                3: 'Wednesday', 4: 'Thursday',
                5: 'Friday', 6: 'Saturday',
                7: 'Sunday'}

    if day in Day_dict.keys():
        day_of_the_week = Day_dict[day]
        print(day_of_the_week)
        speak("The day is " + day_of_the_week)


def tellTime():
    # This method will give the time
    time = str(datetime.datetime.now())

    # the time will be displayed like
    # this "2020-06-05 17:50:14.582630"
    # nd then after slicing we can get time
    print(time)
    hour = time[11:13]
    min = time[14:16]
    speak("The time is sir" + hour + "Hours and" + min + "Minutes")


def Hello():
    speak("Witaj jestem tlumaczem, powiedz z jakiego jezyka mam tlumaczyc: polski czy angielski")


def Take_query():
    while True:
        Hello()
        lang = 'pl-PL'
        while True:
            query = takeCommand(lang).lower()
            if "angielski" in query:
                translator = Translator(from_lang="en", to_lang="pl")
                lang = 'en-US'
                break
            elif "polski" in query:
                translator = Translator(from_lang="pl", to_lang="en")
                lang = 'pl-PL'
                break
            else:
                speak("Nie rozumiem powiedz jeszcze raz:")
        while True:
            query = takeCommand(lang).lower()
            if "bye" in query and lang == 'en-US':
                speak("Bye.")
                exit()
            if "bywaj" in query and lang == 'pl-PL':
                speak("Do zobaczenia")
                exit()
            if "zmień język" in query and lang == 'pl-PL':
                break
            if "change language" in query and lang == 'en-US':
                break
            if (query == "None" or query == "none") and lang == 'pl-PL':
                speak("Nie rozumiem, powiedz jeszcze raz")
                continue
            if (query == "None" or query == "none") and lang == 'en-US':
                speak("I don't understand, please tell me again")
                continue
            try:
                wynik = translator.translate(query)
                speak(wynik)
            except Exception as e:
                print("Błąd usługi tłumaczenia:", e)

if __name__ == '__main__':
    # main method for executing
    # the functions
    Take_query()