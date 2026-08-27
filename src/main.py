import os
import sys
import webbrowser
from datetime import datetime
import speech_recognition as sr
import pyttrx3

engine=pyttrx3.inint()
engine.setProperty('rate',170)

voices=engine.getProperty('voices')
for voice in voices:
    if "female" in  voice.name.lower() or "zira" in voice.name.lower():
        engine.setProperty('voice',voice.id)
        break

    def speak(text):
        print(f"alicia":{text})
        engine.say(text)
        engine.runAndWait()



    def listen():
        recognizer=sr.recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source,duration=0.5)
            try:
                audio=recognizer.listen(source,timeout=6,phrase_time_limit=8)
                text=recognizer.recognize_google(audio).lower()
                return text
            except sr.WaitTimeoutError:
                return ""
            except sr.UnkownValueError:
                return ""
            except sr.RequestError:
                speak("im having trouble connecting to speech recongintion")
                return ""

    def exceute_commands(command):
        if "open youtube " in command:
            webbrowser.open("https://www.youtube.com")
        elif "open  google" in command:
            webbrowser.open("https://www.google.com")
        elif "open notepad " in command:
            os.system("notepad")
        elif "time" in command:
            now=datetime.now().strftime("%I:%M %p")
            speak(f"it is currently "{time})
        elif "shutdown computer" in command:
            os.system("shutdown")
        elif "stop" in command or "exit" in command :
            speak("Goodbye! Call me whenever u need")
            return False
        else:
            speak("i dont have command programmed for that yet ")

        return True


    def main():

    speak("alicia intilized")


    while True:
        phrase=listen()
        if "alicia " in phrase:
            speak("hi hello ! what can i do for you ")

            command=listen()
            if command:
                running=exceute_commands(command)
                if not running:
                    sys.exit()

    if __name__=="__main__":
        main()