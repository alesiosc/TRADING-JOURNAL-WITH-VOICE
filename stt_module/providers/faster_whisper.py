"""FasterWhisper provider implementation"""

from faster_whisper import WhisperModel
from .base import STTProvider


class FasterWhisperProvider(STTProvider):
    """CPU-optimized Whisper transcription provider"""
    
    def __init__(self):
        self.model = None
        self.model_size = "base"
        self.device = "cpu"
        self.compute_type = "int8"  # CPU optimization
        self.language = "en"
    
    def initialize(self, config: dict):
        """Initialize the Whisper model"""
        self.model_size = config.get("model_size", "base")
        self.device = config.get("device", "cpu")
        self.compute_type = config.get("compute_type", "int8")
        self.language = config.get("language", "en")
        
        print(f"Loading Whisper model: {self.model_size} (device={self.device}, compute_type={self.compute_type})")
        
        # Load model (downloads on first run, cached after)
        self.model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type
        )
        
        print("✅ Whisper model loaded successfully")
    
    def transcribe(self, audio_file_path: str) -> str:
        """Transcribe audio file using faster-whisper"""
        if not self.model:
            raise RuntimeError("Model not initialized. Call initialize() first.")
        
        segments, info = self.model.transcribe(
            audio_file_path,
            beam_size=5,
            language=self.language
        )
        
        # Combine all segments into single text
        text = " ".join([segment.text for segment in segments])
        return text.strip()
    
    def cleanup(self):
        """Cleanup model resources"""
        self.model = None
