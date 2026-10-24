import re
import traceback
import pyttsx3
import speech_recognition as sr
import eel
import time
import os

_is_busy = False

def is_busy():
    global _is_busy
    return _is_busy

def speak(text):
    text = str(text)
    print(f"Assistant: {text}")
    try:
        eel.DisplayMessage(text)
        eel.receiverText(text)
    except Exception:
        pass

    try:
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            pass
        engine = pyttsx3.init('sapi5')
        voices = engine.getProperty('voices')
        if len(voices) > 1:
            engine.setProperty('voice', voices[1].id)
        elif len(voices) > 0:
            engine.setProperty('voice', voices[0].id)
        engine.setProperty('rate', 185)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS Error: {e}")

# Global fast recognizer instance
_recognizer = sr.Recognizer()
_recognizer.pause_threshold = 0.5
_recognizer.non_speaking_duration = 0.4
_recognizer.energy_threshold = 280
_recognizer.dynamic_energy_threshold = True

def takecommand():
    with sr.Microphone() as source:
        print("Listening...")
        try:
            eel.DisplayMessage("Listening...")
        except Exception:
            pass

        try:
            audio = _recognizer.listen(source, timeout=5, phrase_time_limit=6)
            print("Recognizing...")
            try:
                eel.DisplayMessage("Recognizing...")
            except Exception:
                pass

            query = _recognizer.recognize_google(audio, language="en-in")
            print("You said:", query)
            return query.lower()

        except sr.WaitTimeoutError:
            print("⏱ Timeout: No speech detected")
            return ""

        except sr.UnknownValueError:
            print("⚠ Could not understand audio")
            return ""

        except sr.RequestError as e:
            print(f"⚠ Speech recognition service error: {e}")
            return ""
        except Exception as e:
            print(f"⚠ Microphone error: {e}")
            return ""


def execute_single_command(query):
    """Executes a single voice or typed command."""
    query = str(query).strip().lower()

    # If user addressed Alexa alone while in active session
    if query in ["alexa", "jarvis", "hey alexa", "hey jarvis"]:
        speak("Yes, I am listening. What can I do for you?")
        return

    # Strip leading assistant name if present (e.g. "alexa open youtube" -> "open youtube")
    query = re.sub(r'^(alexa|jarvis|hey alexa|hey jarvis)\s+', '', query, flags=re.IGNORECASE).strip()

    if not query:
        return

    try:
        eel.senderText(query)
    except Exception:
        pass

    try:
        # --- 1. TIME & DATE ---
        if any(k in query for k in ["what time", "current time", "what is the time"]):
            from engine.system_control import tell_time_and_date
            tell_time_and_date("time", speak)

        elif any(k in query for k in ["today's date", "what is the date", "what date is today", "what day is today"]):
            from engine.system_control import tell_time_and_date
            tell_time_and_date("date", speak)

        # --- 2. SCREENSHOT ---
        elif any(k in query for k in ["screenshot", "capture screen", "take a screenshot"]):
            from engine.system_control import take_screenshot
            take_screenshot(speak)

        # --- 3. SYSTEM STATS & HEALTH ---
        elif any(k in query for k in ["cpu usage", "ram usage", "memory usage", "system info", "system status", "disk space"]):
            from engine.system_control import system_stats
            system_stats(speak)

        # --- 4. SYSTEM POWER (Shutdown, Restart, Sleep, Lock, Cancel) ---
        elif any(k in query for k in ["shutdown pc", "shutdown computer", "turn off pc", "restart pc", "restart computer", "reboot", "lock pc", "lock computer", "sleep pc", "cancel shutdown"]):
            from engine.system_control import system_power
            system_power(query, speak)

        # --- 5. STOP EYE MOUSE ---
        elif any(k in query for k in ["stop eye mouse", "close eye mouse", "exit eye mouse", "stop mouse", "close mouse"]):
            from engine.feature import stop_eyemouse
            stop_eyemouse()

        # --- 6. CLOSE TABS, WINDOWS, OR APPLICATIONS ---
        elif (
            query.startswith("close ")
            or query.startswith("exit ")
            or query.startswith("kill ")
            or query.startswith("quit ")
            or query in ["close", "close tab", "close tabs", "close window", "close this", "close app"]
            or any(k in query for k in [
                "close tab", "close the tab", "close this tab", "close current tab",
                "close tabs", "close all tabs", "close open tabs", "close opened tabs",
                "close window", "close this window", "close active window", "close youtube"
            ])
        ):
            from engine.system_control import close_app
            close_app(query, speak)

        # --- 6. WINDOW MANAGEMENT & BROWSER NAVIGATION ---
        elif any(k in query for k in [
            "new tab", "open tab", "reopen tab", "restore tab", "next tab", "previous tab", "prev tab",
            "refresh page", "reload page", "refresh", "bookmark", "zoom in", "zoom out", "reset zoom",
            "show desktop", "minimize all", "switch window", "alt tab", "maximize", "minimize",
            "snap left", "snap right", "scroll up", "scroll down", "scroll to top", "scroll to bottom"
        ]):
            from engine.system_control import window_control
            window_control(query, speak)

        # --- 7. MEDIA PLAYBACK ---
        elif any(k in query for k in [
            "pause music", "pause audio", "pause song", "pause video", "pause",
            "resume music", "resume", "play music", "play audio",
            "next song", "next track", "next video",
            "previous song", "previous track", "prev song",
            "mute volume", "mute pc", "mute", "unmute"
        ]):
            from engine.system_control import media_control
            media_control(query, speak)

        # --- 8. NOTES & PRODUCTIVITY ---
        elif any(k in query for k in ["take a note", "take note", "save note"]):
            from engine.system_control import take_note
            take_note(query, speak)

        elif any(k in query for k in ["read notes", "show notes", "open notes"]):
            from engine.system_control import read_notes
            read_notes(speak)

        # --- 9. TIMER ---
        elif "timer" in query:
            from engine.system_control import set_timer
            set_timer(query, speak)

        # --- 10. RECYCLE BIN ---
        elif "recycle bin" in query:
            from engine.system_control import empty_recycle_bin
            empty_recycle_bin(speak)

        # --- 11. IP ADDRESS & NETWORK ---
        elif any(k in query for k in ["ip address", "my ip"]):
            from engine.system_control import get_ip_address
            get_ip_address(speak)

        # --- 12. CREATE FOLDER ---
        elif query.startswith("create folder") or query.startswith("make folder"):
            from engine.system_control import create_folder
            create_folder(query, speak)

        # --- 13. DICTATION & TYPING ---
        elif query.startswith("type ") or query.startswith("write "):
            from engine.system_control import type_text
            type_text(query, speak)

        # --- 14. KEYBOARD & MOUSE SHORTCUTS ---
        elif any(k in query for k in ["select all", "press enter", "press esc", "press escape", "fullscreen", "full screen"]):
            from engine.system_control import keyboard_shortcut
            keyboard_shortcut(query, speak)

        elif any(k in query for k in ["double click", "right click"]) or query == "click":
            from engine.system_control import mouse_click
            mouse_click(query, speak)

        # --- 15. GOOGLE SEARCH ---
        elif query.startswith("google ") or query.startswith("search for ") or "search google for" in query:
            from engine.system_control import google_search
            google_search(query, speak)

        # --- 16. OPEN APPLICATION / WEBSITE ---
        elif query.startswith("open ") or query.startswith("launch "):
            from engine.system_control import open_app_or_web
            target = query.replace("open ", "").replace("launch ", "").strip()
            handled = open_app_or_web(target, speak)
            if not handled:
                from engine.feature import openCommand
                openCommand(query)

        # --- 17. SPECIAL FEATURES (Canvas, Camera, Image Gen, Eye Mouse) ---
        elif "canvas" in query:
            from engine.feature import virtual_canvas
            speak("Opening Canvas")
            virtual_canvas()
            
        elif "camera" in query:
            from engine.feature import camera
            speak("Opening Camera")
            camera()
        
        elif "generate image" in query:
            try:
                from engine.feature import image_generate
                speak("Opening Image Generator")
                image_generate()
            except Exception as e:
                speak("Sorry, I couldn't open the Image Generator.")
                print(f"Error opening image generator: {e}")
            
        elif "battery" in query:
            from engine.feature import check_battery
            check_battery()

        elif any(k in query for k in ["eye mouse", "open eye mouse", "start eye mouse", "track eyes"]) or query == "mouse":
            from engine.feature import eyemouse
            speak("Opening Eye Mouse. Press Q, Escape, click the X button, or say close eye mouse to exit.")
            eyemouse()

        # --- 18. VOLUME & BRIGHTNESS ---
        elif "set volume to" in query:
            from engine.feature import set_volume
            try:
                percent = int(''.join([i for i in query if i.isdigit()]))
                set_volume(percent)
                speak(f"Setting volume to {percent} percent.")
            except Exception:
                speak("Sorry, I couldn't understand the volume level.")
                
        elif "set brightness to" in query:
            from engine.feature import set_brightness
            try:
                match = re.search(r'\d+', query)
                if match:
                    percent = int(match.group())
                    if 0 <= percent <= 100:
                        set_brightness(percent)
                        speak(f"Setting brightness to {percent} percent.")
                    else:
                        speak("Please provide a brightness level between 0 and 100.")
                else:
                    speak("Sorry, I couldn't understand the brightness level.")
            except Exception:
                speak("Something went wrong while setting the brightness.")

        elif "volume increase" in query:
            from engine.feature import increase_volume
            increase_volume(10)
            speak("Increasing volume.")

        elif "volume decrease" in query:
            from engine.feature import decrease_volume
            decrease_volume(10)
            speak("Decreasing volume.")

        elif "volume mute" in query:
            from engine.feature import mute_volume
            speak("Volume muted.")

        elif "volume unmute" in query:
            from engine.feature import unmute_volume
            speak("Volume unmuted.")

        # --- 19. YOUTUBE & SONG PLAYBACK ---
        elif (
            "on youtube" in query
            or "youtube" in query
            or query.startswith("play ")
            or query.startswith("listen to ")
        ) and not any(k in query for k in ["play music", "play audio", "pause", "resume", "stop"]):
            from engine.feature import PlayYoutube
            PlayYoutube(query)

        # --- 20. NETWORK SPEED ---
        elif "check internet speed" in query:
            from engine.feature import check_internet_speed
            check_internet_speed()

        # --- 21. EMAIL ---
        elif "send email" in query:
            from engine.feature import send_email
            speak("Who is the recipient? Please provide the email address.")
            to = takecommand()

            speak("What is the subject?")
            subject = takecommand()

            speak("What should I say in the email?")
            content = takecommand()

            send_email(to, subject, content)

        # --- 22. MOBILE / WHATSAPP ---
        elif "send message" in query or "phone call" in query or "video call" in query:
            from engine.feature import findContact, whatsApp, makeCall, sendMessage
            contact_no, name = findContact(query)
            if contact_no != 0:
                speak("Which mode do you want to use? WhatsApp or mobile?")
                preference = takecommand()
                print(f"Selected mode: {preference}")

                if "mobile" in preference:
                    if "send message" in query or "send sms" in query: 
                        speak("What message would you like to send?")
                        msg = takecommand()
                        sendMessage(msg, contact_no, name)
                    elif "phone call" in query:
                        makeCall(name, contact_no)
                    else:
                        speak("Please try again.")
                elif "whatsapp" in preference:
                    flag = ""
                    whatsapp_msg = ""
                    if "send message" in query:
                        flag = 'message'
                        speak("What message would you like to send?")
                        whatsapp_msg = takecommand()
                    else:
                        speak("I cannot make calls on WhatsApp.")
                    whatsApp(contact_no, whatsapp_msg, flag, name)

        # --- 23. AI ASSISTANT CHATBOT (GEMINI) ---
        else:
            from engine.feature import chatBot
            chatBot(query)

    except Exception as e:
        print(f"Error handling command: {e}")
        traceback.print_exc()
        speak("An error occurred while executing the command.")


@eel.expose
def allCommands(message=1):
    """
    Main entrypoint for assistant interactions.
    When triggered by voice, runs a CONTINUOUS LISTENING SESSION:
    - User wakes up Alexa ONCE.
    - Alexa keeps listening and executing commands one after another uninterruptedly!
    - Does NOT require saying 'Alexa' again for follow-up commands!
    - Stays active across tabs, apps, and window switches.
    - Goes back to sleep when user says 'stop listening', 'go to sleep', 'sleep', 'bye',
      or after extended silence (~60 seconds of complete inactivity).
    """
    global _is_busy
    if _is_busy:
        print("Assistant is currently active, ignoring duplicate trigger.")
        return
    _is_busy = True

    try:
        # If text was typed into web UI chatbox:
        if message != 1 and message is not None:
            execute_single_command(str(message).strip())
            return

        # Voice Mode: Continuous Active Listening Session
        try:
            eel.ShowWave()
        except Exception:
            pass

        consecutive_silence = 0
        MAX_SILENCE_CYCLES = 12  # ~60 seconds of complete silence before returning to idle

        print("=== Continuous Listening Session Started ===")
        while True:
            query = takecommand()

            if not query or query.strip() == "":
                consecutive_silence += 1
                if consecutive_silence >= MAX_SILENCE_CYCLES:
                    print("Extended silence detected. Returning to idle sleep mode. Say 'Alexa' to wake me up.")
                    speak("Going back to sleep. Say Alexa when you need me.")
                    break
                continue

            # Command received! Reset the silence counter
            consecutive_silence = 0

            # Check if user commanded to sleep or stop listening
            if any(k in query for k in ["stop listening", "go to sleep", "sleep now", "sleep", "bye", "goodbye", "exit session"]):
                speak("Going to sleep. Say Alexa when you need me.")
                break

            # Execute the voice command
            execute_single_command(query)

            # Ensure the UI wave stays alive for the next command
            try:
                eel.ShowWave()
            except Exception:
                pass

            # Brief pause for audio output to settle before listening for next command
            time.sleep(0.3)

    except Exception as e:
        print(f"Session error: {e}")
        traceback.print_exc()
    finally:
        _is_busy = False
        print("=== Continuous Listening Session Ended ===")
        try:
            eel.ShowHood()
        except Exception:
            pass
