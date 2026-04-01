"""Abstract base class for STT providers"""

from abc import ABC, abstractmethod


class STTProvider(ABC):
    """Abstract base class for speech-to-text providers"""
    
    @abstractmethod
    def transcribe(self, audio_file_path: str) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_file_path: Path to WAV file
            
        Returns:
            Transcribed text string
        """
        pass
    
    @abstractmethod
    def initialize(self, config: dict) -> None:
        """Initialize provider with config"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources"""
        pass
