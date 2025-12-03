import pyaudio

class Microphone:
    def __init__(self, rate=16000, chunk=512):
        self.rate = rate
        self.chunk = chunk
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.is_running = False

    def start(self):
        if self.is_running:
            print("Microphone: Already running")
            return

        try:
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            self.is_running = True
            print(f"Microphone: Started (rate={self.rate}, chunk={self.chunk})")

        except Exception as e:
            print(f"Microphone: FAILED to start - {e}")
            self.is_running = False
            raise

    def read_chunk(self):
        if not self.is_running or not self.stream:
            return None

        try:
            # Windows PyAudio supports overflow handling ONLY inside .read()
            return self.stream.read(self.chunk, exception_on_overflow=False)
        except:
            return None

    def stop(self):
        if not self.is_running:
            return
        self.is_running = False
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        print("Microphone: Stopped")

    def terminate(self):
        self.stop()
        try:
            self.p.terminate()
        except Exception:
            pass
