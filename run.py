import shutil
import subprocess
from main import start

if __name__ == '__main__':
    # Only run ADB initialization if adb executable is available on the system
    if shutil.which("adb"):
        try:
            print("Connecting Android device via ADB...")
            subprocess.run([r'device.bat'], shell=True, timeout=5)
        except Exception as e:
            print(f"Device initialization skipped: {e}")
    else:
        print("ADB not detected on system PATH. Mobile automation features will be disabled.")

    print("Starting Alexa AI Assistant...")
    start()