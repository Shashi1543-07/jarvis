"""
Edge TTS Engine - Natural Neural Voice for Jarvis
Uses Microsoft Edge's neural TTS for smooth, friendly voice output.

Features:
- Async streaming
- Natural neural voice (en-US-GuyNeural)
- Adjustable pitch, rate, volume
- Windows-native playback (no ffmpeg required)
"""
import asyncio
import threading
import queue
import io
import tempfile
import os
import wave
import struct

# Check if edge_tts is available
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("WARNING: edge_tts not installed. Run: pip install edge-tts")


class EdgeTTSEngine:
    """
    Neural TTS engine using Microsoft Edge's voices.
    Provides smooth, natural speech with async streaming.
    """
    
    # Voice options (all neural, natural sounding)
    VOICES = {
        "guy": "en-US-GuyNeural",           # Friendly American male (default)
        "christopher": "en-US-ChristopherNeural",  # Professional American male
        "ryan": "en-GB-RyanNeural",         # British male
        "tony": "en-AU-WilliamNeural",      # Australian male
    }
    
    def __init__(self, voice="guy", on_audio_chunk=None):
        """
        Initialize Edge TTS engine.
        
        Args:
            voice: Voice name key from VOICES dict
            on_audio_chunk: Callback for AEC (receives raw audio bytes)
        """
        self.voice = self.VOICES.get(voice, self.VOICES["guy"])
        self.on_audio_chunk = on_audio_chunk
        
        # Speech queue for async processing
        self.speech_queue = queue.Queue()
        self.is_playing = False
        self.stop_event = threading.Event()
        
        # Voice tuning (faster, energetic tone)
        self.rate = "+25%"    # 1.25x speed for snappy responses
        self.pitch = "+3Hz"   # Slightly higher pitch for friendliness
        self.volume = "+0%"   # Normal volume
        
        # Start worker thread
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        
        print(f"EdgeTTS: Initialized with voice '{self.voice}'")
    
    def speak(self, text: str):
        """Queue text for speaking (non-blocking)."""
        if not text or not text.strip():
            return
            
        # Clear pending speech (interrupt)
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except queue.Empty:
                break
        
        self.stop_event.clear()
        self.speech_queue.put(text)
    
    def stop(self):
        """Stop current speech immediately."""
        self.stop_event.set()
        self.is_playing = False
        
        # Clear queue
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except queue.Empty:
                break
        
        print("EdgeTTS: Stopped")
    
    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        return self.is_playing or not self.speech_queue.empty()
    
    # API compatibility aliases (for AudioEngine)
    def start_tts_stream(self, text: str):
        """Alias for speak() - compatibility with old TextToSpeechEngine API."""
        self.speak(text)
    
    def stop_tts_stream(self):
        """Alias for stop() - compatibility with old TextToSpeechEngine API."""
        self.stop()
    
    def speak_blocking(self, text: str):
        """Speak text and block until complete - for realtime.py compatibility."""
        self.speak(text)
        # Wait for speech to start
        import time
        time.sleep(0.2)
        # Wait for speech to complete
        while self.is_speaking():
            time.sleep(0.1)
    
    def _worker(self):
        """Worker thread - processes speech queue with async event loop."""
        # Create event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while True:
            try:
                text = self.speech_queue.get(timeout=1)
                if text is None:
                    break
                
                self.is_playing = True
                self.stop_event.clear()
                
                # Run async TTS
                loop.run_until_complete(self._speak_async(text))
                
                self.is_playing = False
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"EdgeTTS Worker Error: {e}")
                self.is_playing = False
        
        loop.close()
    
    async def _speak_async(self, text: str):
        """Async TTS with streaming playback."""
        if not EDGE_TTS_AVAILABLE:
            print("EdgeTTS: edge_tts not available, falling back to print")
            print(f"[SPEECH]: {text}")
            return
        
        try:
            # Create communicate object with voice settings
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                pitch=self.pitch,
                volume=self.volume
            )
            
            # Collect audio chunks
            audio_chunks = []
            
            async for chunk in communicate.stream():
                if self.stop_event.is_set():
                    return
                    
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])
            
            # Play collected audio
            if audio_chunks and not self.stop_event.is_set():
                await self._play_audio(b"".join(audio_chunks))
                
        except Exception as e:
            print(f"EdgeTTS Speak Error: {e}")
    
    async def _play_audio(self, audio_data: bytes):
        """Play MP3 audio data using Windows-native methods."""
        temp_mp3 = None
        temp_wav = None
        
        try:
            # Save MP3 to temp file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                f.write(audio_data)
                temp_mp3 = f.name
            
            # Try pygame first (best quality)
            try:
                import pygame
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                
                pygame.mixer.music.load(temp_mp3)
                pygame.mixer.music.play()
                
                # Wait for playback to complete
                while pygame.mixer.music.get_busy():
                    if self.stop_event.is_set():
                        pygame.mixer.music.stop()
                        break
                    await asyncio.sleep(0.1)
                return
                
            except ImportError:
                pass  # pygame not available, try next method
            except Exception as e:
                print(f"EdgeTTS: pygame playback failed: {e}")
            
            # Try pydub with simpleaudio (if available)
            try:
                from pydub import AudioSegment
                import simpleaudio as sa
                
                audio = AudioSegment.from_mp3(temp_mp3)
                play_obj = sa.play_buffer(
                    audio.raw_data, 
                    num_channels=audio.channels,
                    bytes_per_sample=audio.sample_width,
                    sample_rate=audio.frame_rate
                )
                
                while play_obj.is_playing():
                    if self.stop_event.is_set():
                        play_obj.stop()
                        break
                    await asyncio.sleep(0.1)
                return
                
            except ImportError:
                pass  # simpleaudio not available
            except Exception as e:
                print(f"EdgeTTS: simpleaudio playback failed: {e}")
            
            # Fallback: Convert to WAV and use winsound (Windows only)
            try:
                from pydub import AudioSegment
                import winsound
                
                audio = AudioSegment.from_mp3(temp_mp3)
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                    temp_wav = f.name
                
                audio.export(temp_wav, format="wav")
                
                # Play with winsound (blocking but in worker thread so OK)
                winsound.PlaySound(temp_wav, winsound.SND_FILENAME)
                return
                
            except ImportError as e:
                print(f"EdgeTTS: winsound fallback failed (pydub import): {e}")
            except Exception as e:
                print(f"EdgeTTS: winsound fallback failed: {e}")
            
            # Last resort: PowerShell media player
            try:
                import subprocess
                result = subprocess.run(
                    ['powershell', '-c', f'''
                        Add-Type -AssemblyName PresentationCore
                        $player = New-Object System.Windows.Media.MediaPlayer
                        $player.Open([uri]"{temp_mp3}")
                        $player.Play()
                        Start-Sleep -Milliseconds 500
                        while ($player.Position -lt $player.NaturalDuration.TimeSpan) {{
                            Start-Sleep -Milliseconds 100
                        }}
                        $player.Close()
                    '''],
                    capture_output=True,
                    timeout=30
                )
                return
            except Exception as e:
                print(f"EdgeTTS: PowerShell playback failed: {e}")
            
            print("EdgeTTS: No audio playback method available!")
            
        finally:
            # Cleanup temp files
            import time
            time.sleep(0.1)  # Small delay to ensure file is released
            try:
                if temp_mp3 and os.path.exists(temp_mp3):
                    os.unlink(temp_mp3)
            except:
                pass
            try:
                if temp_wav and os.path.exists(temp_wav):
                    os.unlink(temp_wav)
            except:
                pass
    
    def set_voice(self, voice_key: str):
        """Change voice (takes effect on next utterance)."""
        if voice_key in self.VOICES:
            self.voice = self.VOICES[voice_key]
            print(f"EdgeTTS: Voice changed to {self.voice}")
    
    def set_rate(self, rate_percent: int):
        """Set speech rate (-50 to +50 percent)."""
        sign = "+" if rate_percent >= 0 else ""
        self.rate = f"{sign}{rate_percent}%"
    
    def set_pitch(self, pitch_hz: int):
        """Set pitch adjustment in Hz (-50 to +50)."""
        sign = "+" if pitch_hz >= 0 else ""
        self.pitch = f"{sign}{pitch_hz}Hz"
    
    def __del__(self):
        """Cleanup resources."""
        self.speech_queue.put(None)  # Signal worker to stop


# Singleton accessor
_engine_instance = None

def get_tts_engine(on_audio_chunk=None) -> EdgeTTSEngine:
    """Get or create the TTS engine singleton."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = EdgeTTSEngine(on_audio_chunk=on_audio_chunk)
    return _engine_instance
