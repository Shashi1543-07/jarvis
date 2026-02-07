"""Quick test for Edge TTS audio playback"""
import sys
sys.path.insert(0, 'jarvis')

from pydub import AudioSegment
import tempfile
import io
import winsound
import os

print("Testing MP3 load...")
import edge_tts
import asyncio

async def test():
    c = edge_tts.Communicate('Hello, this is a test of the edge TTS system.', 'en-US-GuyNeural')
    data = b''
    async for chunk in c.stream():
        if chunk.get('type') == 'audio':
            data += chunk.get('data', b'')
    return data

d = asyncio.run(test())
print(f'Got {len(d)} bytes of MP3 audio')

# Try to decode with pydub
try:
    audio = AudioSegment.from_mp3(io.BytesIO(d))
    print(f'Decoded OK, duration: {len(audio)} ms')
    
    # Export to WAV and play
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        wav_path = f.name
    
    audio.export(wav_path, format='wav')
    print(f'Exported to WAV: {wav_path}')
    
    print('Playing audio...')
    winsound.PlaySound(wav_path, winsound.SND_FILENAME)
    print('Playback complete!')
    
    os.unlink(wav_path)
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
