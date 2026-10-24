import eel
import time
import threading

from engine.feature import playAssistantSound, hotword
from engine.command import allCommands, speak

def start():
    eel.init("www")
    playAssistantSound()
    
    # Start the hotword listener as a non-daemon persistent worker thread
    hotword_thread = threading.Thread(target=hotword, daemon=False)
    hotword_thread.start()
    
    # Launch Eel UI without terminating when window changes focus or closes
    try:
        eel.start(
            'index.html',
            mode='edge',
            host='localhost',
            block=True,
            close_callback=lambda page, sockets: None
        )
    except Exception as e:
        print(f"UI window closed or running in background: {e}")
    
    print("Alexa Voice Assistant is continuously active in the background. Say 'Alexa' anytime...")
    # Keep the assistant alive indefinitely
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down assistant.")

if __name__ == '__main__':
    start()
