import os
import re
import time
import struct
import sqlite3
import subprocess
import webbrowser
from urllib.parse import quote
from pathlib import Path

import eel

from engine.command import speak
from engine.config import ASSISTANT_NAME, GENAI_API_KEY, EMAIL_ADDRESS, EMAIL_PASSWORD, PORCUPINE_ACCESS_KEY
from engine.helper import extract_yt_term, remove_words

# Resolve database path relative to project root
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "jarvis.db")

def get_db():
    return sqlite3.connect(DB_PATH)

@eel.expose
def playAssistantSound():
    import threading
    def _play():
        try:
            from playsound import playsound
            sound_path = str(BASE_DIR / "www" / "assets" / "audio" / "start_sound.mp3")
            if os.path.exists(sound_path):
                playsound(sound_path)
        except Exception as e:
            print(f"Could not play assistant sound: {e}")
    threading.Thread(target=_play, daemon=True).start()

def openCommand(query):
    query = query.replace(ASSISTANT_NAME, "")
    query = query.replace("open", "")
    app_name = query.strip().lower()

    if not app_name:
        return

    try:
        con = get_db()
        cursor = con.cursor()
        cursor.execute('SELECT path FROM sys_command WHERE LOWER(name) = ?', (app_name,))
        results = cursor.fetchall()

        if len(results) != 0:
            speak(f"Opening {app_name}")
            os.startfile(results[0][0])
            con.close()
            return

        cursor.execute('SELECT url FROM web_command WHERE LOWER(name) = ?', (app_name,))
        results = cursor.fetchall()
        con.close()

        if len(results) != 0:
            speak(f"Opening {app_name}")
            webbrowser.open(results[0][0])
            return

        speak(f"Opening {app_name}")
        try:
            os.system(f'start {app_name}')
        except Exception:
            speak("Application or website not found")
    except Exception as e:
        print(f"openCommand error: {e}")
        speak("Something went wrong while opening the application")

def PlayYoutube(query):
    try:
        import pywhatkit as kit
        clean = query.lower()
        for prefix in ["search for", "search", "play", "listen to", "find"]:
            if clean.startswith(prefix):
                clean = clean[len(prefix):].strip()
        clean = clean.replace("on youtube", "").replace("in youtube", "").strip()
        search_term = clean if clean else "trending songs"
        speak(f"Playing {search_term} on YouTube")
        kit.playonyt(search_term)
    except Exception as e:
        print(f"PlayYoutube error: {e}")
        speak("Could not play on YouTube")

def hotword():
    porcupine = None
    paud = None
    audio_stream = None

    try:
        import pvporcupine
        import pyaudio

        if PORCUPINE_ACCESS_KEY:
            porcupine = pvporcupine.create(access_key=PORCUPINE_ACCESS_KEY, keywords=["alexa"])
        else:
            porcupine = pvporcupine.create(keywords=["alexa"])

        paud = pyaudio.PyAudio()
        audio_stream = paud.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        from engine.command import is_busy, allCommands

        print("Hotword listener started. Say 'Alexa'...")
        while True:
            if is_busy():
                time.sleep(0.3)
                continue

            keyword = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            keyword = struct.unpack_from("h" * porcupine.frame_length, keyword)
            keyword_index = porcupine.process(keyword)

            if keyword_index >= 0:
                if is_busy():
                    continue
                print("Hotword 'Alexa' detected!")
                try:
                    try:
                        eel.ShowWave()
                    except Exception:
                        pass
                    playAssistantSound()
                    allCommands()
                except Exception as e:
                    print(f"Error handling hotword: {e}")

    except Exception as e:
        print(f"Hotword detection exception: {e}")
    finally:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if paud is not None:
            paud.terminate()

def findContact(query):
    words_to_remove = [
        ASSISTANT_NAME.lower(), 'make', 'image', 'a', 'to', 'phone',
        'call', 'send', 'message', 'whatsapp', 'video', 'tell', 'internet', 'me'
    ]
    query = remove_words(query, words_to_remove).strip().lower()

    if not query:
        speak("Who would you like to contact?")
        return 0, 0

    try:
        con = get_db()
        cursor = con.cursor()
        cursor.execute(
            "SELECT mobile_no, name FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?",
            ('%' + query + '%', query + '%')
        )
        results = cursor.fetchall()
        con.close()

        if results:
            mobile_number_str = str(results[0][0]).replace(" ", "").replace("-", "")
            contact_name = results[0][1] if len(results[0]) > 1 else query
            if not mobile_number_str.startswith('+91'):
                mobile_number_str = '+91' + mobile_number_str
            return mobile_number_str, contact_name

        speak("Contact does not exist in contacts list")
        return 0, 0
    except Exception as e:
        print(f"findContact error: {e}")
        speak("Failed to query contacts")
        return 0, 0

def whatsApp(mobile_no, message, flag, name):
    try:
        import pyautogui
        if flag == 'message':
            encoded_message = quote(message)
            whatsapp_url = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"
            subprocess.run(f'start "" "{whatsapp_url}"', shell=True)
            time.sleep(6)
            pyautogui.press('enter')
            time.sleep(1)
            speak(f"Message sent successfully to {name}")
        else:
            speak(f"Cannot make a call to {name} via WhatsApp")
    except Exception as e:
        print(f"WhatsApp error: {e}")
        speak("Could not send WhatsApp message")

def makeCall(name, mobileNo):
    try:
        mobileNo = str(mobileNo).replace(" ", "").replace("+", "")
        speak(f"Calling {name}")
        command = f'adb shell am start -a android.intent.action.CALL -d tel:{mobileNo}'
        os.system(command)
    except Exception as e:
        print(f"makeCall error: {e}")
        speak("Could not initiate phone call via ADB")

def sendMessage(message, mobileNo, name):
    try:
        from engine.helper import replace_spaces_with_percent_s, goback, keyEvent, tapEvents, adbInput
        message = replace_spaces_with_percent_s(message)
        mobileNo = replace_spaces_with_percent_s(str(mobileNo))
        speak("Sending message")
        goback(4)
        time.sleep(1)
        keyEvent(3)
        tapEvents(435, 2235)
        tapEvents(937, 2217)
        adbInput(mobileNo)
        tapEvents(306, 670)
        tapEvents(953, 1256)
        adbInput(message)
        tapEvents(972, 1275)
        speak(f"Message sent successfully to {name}")
    except Exception as e:
        print(f"sendMessage error: {e}")
        speak("Failed to send SMS")

# Intelligent AI Agent implementation using Google Generative AI and Dynamic Tools
def chatBot(query):
    if not query or not query.strip():
        return
    try:
        from engine.agent import get_agent
        agent = get_agent()
        return agent.run(query)
    except Exception as e:
        print(f"chatBot/Agent error: {e}")
        speak("I am having trouble answering that right now.")

NIRCMD_PATH = str(BASE_DIR / "nircmd.exe")

# Volume controls
def set_volume(percent):
    try:
        percent = max(0, min(100, int(percent)))
        volume = int((percent / 100) * 65535)
        subprocess.run(f'"{NIRCMD_PATH}" setsysvolume {volume}', shell=True)
    except Exception as e:
        print(f"set_volume error: {e}")

def increase_volume(amount=10):
    try:
        change = int((amount / 100) * 65535)
        subprocess.run(f'"{NIRCMD_PATH}" changesysvolume {change}', shell=True)
    except Exception as e:
        print(f"increase_volume error: {e}")

def decrease_volume(amount=10):
    try:
        change = int((amount / 100) * 65535)
        subprocess.run(f'"{NIRCMD_PATH}" changesysvolume -{change}', shell=True)
    except Exception as e:
        print(f"decrease_volume error: {e}")

def mute_volume():
    subprocess.run(f'"{NIRCMD_PATH}" mutesysvolume 1', shell=True)

def unmute_volume():
    subprocess.run(f'"{NIRCMD_PATH}" mutesysvolume 0', shell=True)

def set_brightness(level_percent):
    try:
        import screen_brightness_control as sbc
        sbc.set_brightness(level_percent)
    except Exception as e:
        print(f"set_brightness error: {e}")

def check_battery():
    try:
        import psutil
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            is_plugged = battery.power_plugged
            status = "charging" if is_plugged else "not charging"
            speak(f"Battery is at {percent} percent and it is currently {status}.")
        else:
            speak("No battery detected on this system.")
    except Exception as e:
        print(f"check_battery error: {e}")
        speak("Could not retrieve battery status.")

def check_internet_speed():
    try:
        import speedtest
        speak("Checking internet speed, please wait a moment.")
        st = speedtest.Speedtest()
        st.get_best_server()
        download_speed = st.download() / 1_000_000
        upload_speed = st.upload() / 1_000_000
        ping = st.results.ping
        speak(f"Download speed is {download_speed:.2f} Mbps, upload speed is {upload_speed:.2f} Mbps, and ping is {ping:.0f} ms.")
    except Exception as e:
        print(f"check_internet_speed error: {e}")
        speak("Could not check internet speed.")

def send_email(to, subject, message_body):
    import smtplib
    from email.message import EmailMessage

    clean_to = str(to).lower().replace(" at ", "@").replace(" dot ", ".").replace(" ", "").strip()
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = clean_to
    msg.set_content(message_body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
            speak("Email has been sent successfully.")
    except Exception as e:
        print(f"send_email error: {e}")
        speak("Sorry, I was not able to send the email.")

# Lazy-loaded GUI features
def camera():
    try:
        import cv2
        import tkinter as tk
        from PIL import Image, ImageTk

        cap = cv2.VideoCapture(0)
        camera_roll = Path.home() / "Pictures" / "Camera Roll"
        camera_roll.mkdir(parents=True, exist_ok=True)

        window = tk.Tk()
        window.title("Webcam Photo Capture")

        label = tk.Label(window)
        label.pack()

        def capture_photo():
            ret, frame = cap.read()
            if ret:
                image_path = camera_roll / f"captured_photo_{int(time.time())}.jpg"
                cv2.imwrite(str(image_path), frame)
                print(f"Image saved at: {image_path}")
                speak("Image captured successfully")

        def show_image(frame):
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            label.imgtk = imgtk
            label.configure(image=imgtk)

        def update_frame():
            ret, frame = cap.read()
            if ret:
                show_image(frame)
            window.after(10, update_frame)

        btn = tk.Button(window, text="Capture Photo", font=("Arial", 14), command=capture_photo)
        btn.pack(pady=10)

        update_frame()
        window.mainloop()
        cap.release()
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"camera error: {e}")
        speak("Could not open the camera.")

def virtual_canvas():
    try:
        import cv2
        import numpy as np
        import mediapipe as mp

        mp_hands = mp.solutions.hands
        mp_draw = mp.solutions.drawing_utils
        hands = mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.8)

        canvas = np.ones((480, 640, 3), dtype=np.uint8) * 255
        color = (0, 0, 255)

        cap = cv2.VideoCapture(0)
        prev_x, prev_y = None, None

        buttons = [
            (50, "Red", (0, 0, 255)),
            (120, "Blue", (255, 0, 0)),
            (190, "Black", (0, 0, 0)),
            (260, "Green", (0, 255, 0)),
            (330, "Clear", (128, 128, 128)),
            (400, "Close", (0, 0, 0))
        ]

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            for y, text, col in buttons:
                cv2.rectangle(frame, (10, y), (100, y + 50), col, -1)
                cv2.putText(frame, text, (15, y + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    index_finger = hand_landmarks.landmark[8]
                    h, w, _ = frame.shape
                    x, y = int(index_finger.x * w), int(index_finger.y * h)

                    if 10 <= x <= 100:
                        if 50 <= y <= 100:
                            color = (0, 0, 255)
                        elif 120 <= y <= 170:
                            color = (255, 0, 0)
                        elif 190 <= y <= 240:
                            color = (0, 0, 0)
                        elif 260 <= y <= 310:
                            color = (0, 255, 0)
                        elif 330 <= y <= 380:
                            canvas = np.ones((480, 640, 3), dtype=np.uint8) * 255
                        elif 400 <= y <= 450:
                            cap.release()
                            cv2.destroyAllWindows()
                            return
                    else:
                        if prev_x is not None and prev_y is not None:
                            cv2.line(canvas, (prev_x, prev_y), (x, y), color, 5)
                        prev_x, prev_y = x, y

                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            else:
                prev_x, prev_y = None, None

            cv2.imshow("Camera Feed", frame)
            cv2.imshow("Canvas", canvas)

            key = cv2.waitKey(1) & 0xFF
            if key in [ord('q'), ord('Q'), 27]:
                break
            try:
                if cv2.getWindowProperty("Canvas", cv2.WND_PROP_VISIBLE) < 1:
                    break
            except Exception:
                pass

        cap.release()
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"virtual_canvas error: {e}")
        speak("Could not open the virtual canvas.")

_eyemouse_running = False
_eyemouse_thread = None

def stop_eyemouse():
    """Stops the eye-controlled mouse thread and closes its OpenCV window."""
    global _eyemouse_running
    if not _eyemouse_running:
        speak("Eye mouse is not currently running.")
        return
    _eyemouse_running = False
    try:
        import cv2
        cv2.destroyAllWindows()
    except Exception:
        pass
    speak("Eye mouse stopped.")

def eyemouse():
    """Launches eye-controlled mouse in a background thread so assistant remains responsive."""
    global _eyemouse_running, _eyemouse_thread
    if _eyemouse_running:
        speak("Eye mouse is already running. Say close eye mouse or press Q or Escape to close it.")
        return

    _eyemouse_running = True

    def _loop():
        global _eyemouse_running
        cam = None
        try:
            import cv2
            import pyautogui
            import mediapipe as mp

            cam = cv2.VideoCapture(0)
            face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
            screen_w, screen_h = pyautogui.size()
            window_name = 'Eye Controlled Mouse (Press Q or Esc to exit)'

            while _eyemouse_running:
                ret, frame = cam.read()
                if not ret:
                    break
                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                output = face_mesh.process(rgb_frame)
                landmark_points = output.multi_face_landmarks
                frame_h, frame_w, _ = frame.shape

                if landmark_points:
                    landmarks = landmark_points[0].landmark
                    for id_idx, landmark in enumerate(landmarks[474:478]):
                        x = int(landmark.x * frame_w)
                        y = int(landmark.y * frame_h)
                        cv2.circle(frame, (x, y), 3, (0, 255, 0))
                        if id_idx == 1:
                            screen_x = screen_w * landmark.x
                            screen_y = screen_h * landmark.y
                            pyautogui.moveTo(screen_x, screen_y)

                    left = [landmarks[145], landmarks[159]]
                    for landmark in left:
                        x = int(landmark.x * frame_w)
                        y = int(landmark.y * frame_h)
                        cv2.circle(frame, (x, y), 3, (0, 255, 255))

                    if (left[0].y - left[1].y) < 0.004:
                        pyautogui.click()
                        pyautogui.sleep(1)

                cv2.imshow(window_name, frame)
                key = cv2.waitKey(1) & 0xFF
                if key in [ord('q'), ord('Q'), 27]:
                    break
                try:
                    if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                        break
                except Exception:
                    pass

        except Exception as e:
            print(f"eyemouse error: {e}")
        finally:
            _eyemouse_running = False
            if cam:
                cam.release()
            try:
                import cv2
                cv2.destroyAllWindows()
            except Exception:
                pass

    import threading
    _eyemouse_thread = threading.Thread(target=_loop, daemon=True)
    _eyemouse_thread.start()

def image_generate():
    try:
        import tkinter as tk
        import customtkinter as ctk
        from PIL import ImageTk
        import torch
        from diffusers import StableDiffusionPipeline
        from engine.config import HF_TOKEN

        app = tk.Tk()
        app.geometry("532x632")
        app.title("AI Image Generator")
        ctk.set_appearance_mode("dark")

        prompt = ctk.CTkEntry(
            master=app,
            height=40,
            width=512,
            font=("Arial", 16),
            text_color="black",
            fg_color="white"
        )
        prompt.place(x=10, y=10)

        lmain = ctk.CTkLabel(master=app, height=512, width=512, text="")
        lmain.place(x=10, y=110)

        speak("Loading image generation model, please wait.")
        modelid = "CompVis/stable-diffusion-v1-4"
        pipe = StableDiffusionPipeline.from_pretrained(
            modelid,
            torch_dtype=torch.float32,
            use_auth_token=HF_TOKEN
        )
        pipe.to("cpu")

        def generate():
            text = prompt.get()
            if not text:
                return
            speak("Generating image, this may take a moment on CPU.")
            image = pipe(text, guidance_scale=8.5).images[0]
            save_path = BASE_DIR / "generatedimage.png"
            image.save(str(save_path))
            img = ImageTk.PhotoImage(image)
            lmain.configure(image=img)
            lmain.image = img
            speak("Image generated successfully")

        trigger = ctk.CTkButton(
            master=app,
            height=40,
            width=120,
            font=("Arial", 16),
            text_color="white",
            fg_color="blue",
            text="Generate",
            command=generate
        )
        trigger.place(x=206, y=60)
        app.mainloop()
    except Exception as e:
        print(f"image_generate error: {e}")
        speak("Image generator failed to launch.")
