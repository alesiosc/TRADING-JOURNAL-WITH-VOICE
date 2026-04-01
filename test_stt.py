import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stt_module import create_stt_module
from stt_module.audio_capture import AudioCapture

def main():
    print("=" * 60)
    print("STT MODULE TEST")
    print("=" * 60)
    
    print("\n1. Listing available microphones:")
    AudioCapture.list_devices()
    
    print("\n2. Initializing STT module...")
    stt = create_stt_module("config.yaml")
    
    print("\n3. Starting STT module...")
    stt.start()
    
    print("\n" + "=" * 60)
    print("READY!")
    print("=" * 60)
    print("\nPress Shift+Tab to START recording")
    print("Speak your message...")
    print("Press Shift+Tab again to STOP and transcribe")
    print("\nPress Ctrl+C to exit\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        stt.cleanup()
        print("Goodbye!")

if __name__ == "__main__":
    main()
