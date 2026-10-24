import pyaudio

def test_microphone():
    p = pyaudio.PyAudio()
    device_index = 1  # Try changing this index based on the list from the previous step

    try:
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=44100,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=1024)
        print("Microphone is working. Listening...")
        data = stream.read(1024)
        stream.stop_stream()
        stream.close()
    except Exception as e:
        print(f"Error with microphone: {e}")
    finally:
        p.terminate()

test_microphone()
