"""Audio capture using pyaudio"""

import pyaudio
import wave
import tempfile
import os


class AudioCapture:
    """Handles microphone recording and WAV file creation"""
    
    def __init__(self, device_index=None, sample_rate=16000, channels=1):
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = 1024
        self.format = pyaudio.paInt16
        
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
    
    def start_recording(self):
        """Start capturing audio from microphone"""
        self.frames = []
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=self.chunk
        )
        print("🎤 Recording started...")
    
    def stop_recording(self) -> str:
        """Stop recording and save to temp WAV file"""
        print("⏹️  Recording stopped.")
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        # Save to temp file
        fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        
        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))
        
        return temp_path
    
    def record_chunk(self):
        """Record one chunk (called in loop while recording)"""
        if self.stream:
            data = self.stream.read(self.chunk, exception_on_overflow=False)
            self.frames.append(data)
    
    def cleanup(self):
        """Cleanup audio resources"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
    
    @staticmethod
    def list_devices():
        """List available microphone devices"""
        audio = pyaudio.PyAudio()
        print("\nAvailable microphone devices:")
        for i in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  [{i}] {info['name']}")
        audio.terminate()
