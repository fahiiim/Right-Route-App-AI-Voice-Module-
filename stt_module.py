"""
Speech-to-Text Module for Route Instructions
Captures audio from microphone and converts to text using Google Cloud API
"""

import sounddevice as sd
import numpy as np
from google.cloud import speech_v1
from config import get_speech_client, STT_CONFIG
from route_parser import extract_routes, format_route_output

try:
    import noisereduce as nr
except ImportError:
    nr = None


class SpeechToTextModule:
    """Handles microphone input and Google Cloud STT processing"""
    
    def __init__(self, max_duration_seconds=180, silence_threshold=10, chunk_size=1024):
        """
        Initialize STT module
        
        Args:
            max_duration_seconds: Maximum recording duration (default 3 minutes)
            silence_threshold: Stop recording after N seconds of silence (default 10)
            chunk_size: Audio buffer size
        """
        self.max_duration_seconds = max_duration_seconds
        self.silence_threshold = silence_threshold
        self.chunk_size = chunk_size
        self.sample_rate = STT_CONFIG['sample_rate_hertz']
        self.client = get_speech_client()
        
    def _generator(self, audio_data, chunk_size):
        """Generator for streaming audio chunks"""
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i:i + chunk_size]
    
    def preprocess_audio(self, audio_array):
        """Preprocess audio to improve STT accuracy - remove background noise"""
        try:
            # Convert to float32 for processing
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # Aggressive noise reduction
            if nr is not None:
                # Use stationary mode for constant background noise
                reduced_noise = nr.reduce_noise(
                    y=audio_float, 
                    sr=self.sample_rate,
                    stationary=True,
                    prop_decrease=0.95  # Aggressive noise reduction
                )
            else:
                reduced_noise = audio_float
            
            # Apply simple high-pass filter to remove rumble
            from scipy import signal
            # 300 Hz high-pass filter (removes low-frequency noise)
            sos = signal.butter(4, 300, 'hp', fs=self.sample_rate, output='sos')
            filtered = signal.sosfilt(sos, reduced_noise)
            
            # Apply gentle low-pass to remove high-frequency hiss (around 7kHz)
            sos_lp = signal.butter(4, 7000, 'lp', fs=self.sample_rate, output='sos')
            filtered = signal.sosfilt(sos_lp, filtered)
            
            # Normalize audio
            max_val = np.max(np.abs(filtered))
            if max_val > 0:
                filtered = filtered / max_val
            
            # Convert back to int16
            audio_processed = (filtered * 32767).astype(np.int16)
            return audio_processed.tobytes()
            
        except Exception as e:
            print(f"[WARNING] Audio preprocessing simplified: {str(e)}\n")
            return audio_array.tobytes()
    
    def record_audio(self):
        """
        Record audio from microphone with intelligent speech detection
        Only captures clear speech, ignores background noise
        
        Returns:
            bytes: Raw audio data in LINEAR16 format
        """
        print(f"[RECORDING] Max {self.max_duration_seconds}s, auto-stop after {self.silence_threshold}s silence\n")
        
        frames = []
        silence_counter = 0
        max_frames = int(self.sample_rate / self.chunk_size * self.max_duration_seconds)
        silence_frames_limit = int(self.sample_rate / self.chunk_size * self.silence_threshold)
        speech_threshold = 500  # Higher threshold - only capture clear speech (was 100)
        
        print("Speak clearly... Background noise will be ignored.\n")
        
        stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            blocksize=self.chunk_size,
            dtype=np.int16
        )
        
        try:
            with stream:
                frame_count = 0
                while frame_count < max_frames:
                    data, _ = stream.read(self.chunk_size)
                    frames.append(data.copy())
                    
                    # Calculate RMS for sound level detection
                    rms = np.sqrt(np.mean(data.astype(np.float32) ** 2))
                    
                    # Intelligent speech detection - only clear speech (high RMS)
                    if rms < speech_threshold:
                        silence_counter += 1
                    else:
                        silence_counter = 0  # Reset on speech detection
                    
                    # Stop if silence threshold reached
                    if silence_counter >= silence_frames_limit:
                        print("\n[SILENCE DETECTED] Recording stopped\n")
                        break
                    
                    frame_count += 1
        except KeyboardInterrupt:
            print("\n[INTERRUPTED] Recording stopped\n")
        
        if frames:
            audio_array = np.concatenate(frames, axis=0)
            # Aggressive preprocessing to remove all noise
            audio_bytes = self.preprocess_audio(audio_array)
        else:
            audio_bytes = b''
        
        print("[RECORDING] Complete\n")
        return audio_bytes
    
    def transcribe_audio(self, audio_data):
        """
        Send audio to Google Cloud STT and get transcription
        Uses standard recognition first for complex route data
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            str: Transcribed text
        """
        if not audio_data:
            print("[ERROR] No audio data to process\n")
            return None
        
        print("[PROCESSING] Google Cloud STT...\n")
        
        try:
            # First try: Standard recognition (better for complex content)
            config = speech_v1.RecognitionConfig(
                encoding=STT_CONFIG['encoding'],
                sample_rate_hertz=self.sample_rate,
                language_code=STT_CONFIG['language_code'],
                enable_automatic_punctuation=True,
                use_enhanced=True,
                model='video',  # Better for long-form audio
                speech_contexts=[
                    speech_v1.SpeechContext(phrases=[
                        'INTERSECTION', 'STATE BORDER', 'NORTHBOUND', 'SOUTHBOUND',
                        'EASTBOUND', 'WESTBOUND', 'START ON', 'END ON', 'AT',
                        'IN', 'SB', 'EB', 'NB', 'WB', 'A10', 'B62', 'QUAIL AVE',
                        'LYON', 'ROCK RAPIDS', 'SANBORN', 'EMMETSBURG', 'HANCOCK',
                        'UNION STREET', 'EASTERN STREET', 'BROADWAY'
                    ])
                ]
            )
            
            audio = speech_v1.RecognitionAudio(content=audio_data)
            response = self.client.recognize(config=config, audio=audio)
            
            if response.results and response.results[0].alternatives:
                transcript = response.results[0].alternatives[0].transcript
                print("[INFO] Used standard recognition (better for complex content)\n")
                return transcript
                
        except Exception as e:
            print(f"[WARNING] Standard recognition: {str(e)}\n")
        
        # Fallback: Streaming recognition
        try:
            print("[INFO] Falling back to streaming recognition...\n")
            
            config = speech_v1.RecognitionConfig(
                encoding=STT_CONFIG['encoding'],
                sample_rate_hertz=self.sample_rate,
                language_code=STT_CONFIG['language_code'],
                enable_automatic_punctuation=True,
                use_enhanced=True,
                model='video',
                speech_contexts=[
                    speech_v1.SpeechContext(phrases=[
                        'INTERSECTION', 'STATE BORDER', 'NORTHBOUND', 'SOUTHBOUND',
                        'EASTBOUND', 'WESTBOUND', 'START ON', 'END ON', 'AT',
                        'IN', 'SB', 'EB', 'NB', 'WB', 'A10', 'B62', 'QUAIL AVE',
                        'LYON', 'ROCK RAPIDS', 'SANBORN', 'EMMETSBURG', 'HANCOCK',
                        'UNION STREET', 'EASTERN STREET', 'BROADWAY'
                    ])
                ]
            )
            
            streaming_config = speech_v1.StreamingRecognitionConfig(config=config)
            
            # Use smaller chunks for streaming
            chunk_size = 4096
            requests = (speech_v1.StreamingRecognizeRequest(audio_content=chunk) 
                      for chunk in self._generator(audio_data, chunk_size))
            
            responses = self.client.streaming_recognize(streaming_config, requests)
            
            transcript = ''
            for response in responses:
                if not response.results:
                    continue
                
                result = response.results[0]
                if not result.is_final:
                    continue
                
                transcript += result.alternatives[0].transcript + ' '
            
            return transcript.strip()
            
        except Exception as e2:
            print(f"[ERROR] Streaming recognition failed: {str(e2)}\n")
            return None
    
    def process_route_instructions(self):
        """
        Main function: Record audio, transcribe, and extract route information
        
        Returns:
            dict: Structured route data with sequential route segments
        """
        try:
            audio_data = self.record_audio()
            transcribed_text = self.transcribe_audio(audio_data)
            
            if transcribed_text:
                print("\n[OUTPUT] Transcribed Text:")
                print(f"{transcribed_text}\n")
                
                # Extract route information using OpenAI
                route_data = extract_routes(transcribed_text)
                
                if route_data:
                    formatted_output = format_route_output(route_data)
                    print(formatted_output)
                    return route_data
                else:
                    print("[ERROR] Could not extract route information\n")
                    return None
            else:
                print("[ERROR] No speech detected. Please try again.")
                return None
                
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return None


def main():
    """Entry point"""
    stt = SpeechToTextModule()
    result = stt.process_route_instructions()
    return result


if __name__ == "__main__":
    main()
