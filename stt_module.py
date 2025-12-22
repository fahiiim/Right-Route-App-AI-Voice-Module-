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
    
    def __init__(self, max_duration_seconds=180, silence_threshold=3.5, chunk_size=4096):
        """
        Initialize STT module
        
        Args:
            max_duration_seconds: Maximum recording duration (default 3 minutes)
            silence_threshold: Stop recording after N seconds of silence (default 3.5 - allows natural speech pauses)
            chunk_size: Audio buffer size (larger buffer for better noise detection)
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
        """Minimal preprocessing to preserve speech quality while removing obvious noise"""
        try:
            # Ensure we have enough data
            if len(audio_array) < 1024:
                print(f"[INFO] Audio short, returning as-is\n")
                return audio_array.tobytes()
            
            # Convert to float32
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # LIGHT noise reduction only if available
            if nr is not None:
                try:
                    reduced_noise = nr.reduce_noise(
                        y=audio_float, 
                        sr=self.sample_rate,
                        stationary=True,
                        prop_decrease=0.5  # Very light - preserve speech
                    )
                except:
                    reduced_noise = audio_float
            else:
                reduced_noise = audio_float
            
            # Gentle high-pass filter ONLY (remove true rumble)
            from scipy import signal
            try:
                sos = signal.butter(2, 100, 'hp', fs=self.sample_rate, output='sos')
                filtered = signal.sosfilt(sos, reduced_noise)
            except:
                filtered = reduced_noise
            
            # Soft normalization
            max_val = np.max(np.abs(filtered))
            if max_val > 0:
                filtered = filtered / max_val * 0.98
            else:
                filtered = reduced_noise
            
            # Convert back to int16
            audio_processed = (filtered * 32767).astype(np.int16)
            return audio_processed.tobytes()
            
        except Exception as e:
            print(f"[INFO] Using original audio: {str(e)}\n")
            return audio_array.tobytes()
    
    def record_audio(self):
        """
        Record audio from microphone with intelligent speech detection
        Uses adaptive silence detection to capture complete route instructions
        
        Returns:
            bytes: Raw audio data in LINEAR16 format
        """
        print(f"[RECORDING] Max {self.max_duration_seconds}s, auto-stop after {self.silence_threshold}s silence\n")
        
        frames = []
        silence_duration = 0
        has_detected_speech = False
        max_frames = int(self.sample_rate / self.chunk_size * self.max_duration_seconds)
        silence_frames_limit = int(self.sample_rate / self.chunk_size * self.silence_threshold)
        
        # Adaptive threshold: requires 1500 RMS to detect real speech (sensitive to human voice)
        speech_threshold = 1500
        # Continuous speech indicator: track recent activity
        recent_speech_frames = 0
        
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
                    
                    # Calculate RMS energy for accurate speech detection
                    rms = np.sqrt(np.mean(data.astype(np.float32) ** 2))
                    
                    # Multi-stage detection:
                    if rms >= speech_threshold:
                        silence_duration = 0
                        has_detected_speech = True
                        recent_speech_frames = 5  # Keep buffer of recent speech
                    else:
                        # Decrement recent speech tracker
                        if recent_speech_frames > 0:
                            recent_speech_frames -= 1
                        # Only count silence if no recent speech activity
                        if has_detected_speech and recent_speech_frames == 0:
                            silence_duration += 1
                    
                    # Stop only after sustained silence at the END of speaking
                    if has_detected_speech and silence_duration >= silence_frames_limit and recent_speech_frames == 0:
                        print("\n[SILENCE DETECTED] Recording stopped\n")
                        break
                    
                    frame_count += 1
        except KeyboardInterrupt:
            print("\n[INTERRUPTED] Recording stopped\n")
        
        if frames:
            audio_array = np.concatenate(frames, axis=0)
            print(f"[DEBUG] Total audio captured: {len(audio_array)} samples ({len(audio_array)/self.sample_rate:.2f} seconds)\n")
            # Minimal preprocessing - preserve audio quality
            audio_bytes = self.preprocess_audio(audio_array)
            print(f"[DEBUG] Audio after preprocessing: {len(audio_bytes)} bytes\n")
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
        
        print(f"[DEBUG] Audio size: {len(audio_data)} bytes\n")
        print("[PROCESSING] Google Cloud STT...\n")
        
        try:
            # Use latest_long model - best for structured and command-heavy content
            config = speech_v1.RecognitionConfig(
                encoding=STT_CONFIG['encoding'],
                sample_rate_hertz=self.sample_rate,
                language_code=STT_CONFIG['language_code'],
                enable_automatic_punctuation=True,
                use_enhanced=True,
                model='latest_long',  # Best model for route data and navigation
                speech_contexts=[
                    speech_v1.SpeechContext(
                        phrases=[
                            # Route numbers - most critical
                            'I-29', 'I-35', 'I-90', 'I-80', 'I-70', 'I-480',
                            'US-75', 'US-59', 'US-18', 'US-69', 'US-20', 'US-30',
                            'IA-9', 'IA-4', 'IA-3', 'IA-27', 'IA-175',
                            'B-62', 'B62', 'A-10', 'A10',
                            # Directional suffixes
                            'NORTHBOUND', 'SOUTHBOUND', 'EASTBOUND', 'WESTBOUND',
                            'NB', 'SB', 'EB', 'WB', 'NORTH', 'SOUTH', 'EAST', 'WEST',
                            # Intersection markers
                            'INTERSECTION', 'AT INTERSECTION', 'MILEPOST', 'MP',
                            'STATE BORDER', 'JUNCTION', 'EXIT', 'MILE MARKER',
                            # Action commands
                            'START ON', 'START AT', 'END ON', 'END AT', 'END UP',
                            'CONTINUE', 'TURN', 'MERGE', 'TAKE',
                            'AT', 'IN', 'NEAR', 'TOWARDS',
                            # City and location names
                            'LYON', 'ROCK RAPIDS', 'SANBORN', 'EMMETSBURG', 
                            'HANCOCK', 'SIOUX CITY', 'SPENCER', 'ESTHERVILLE',
                            'CHEROKEE', 'STORM LAKE', 'TOLEDO', 'MAPLETON',
                            'WASHTA', 'DUNLAP', 'DENISON', 'CRAWFORD',
                            # Street names
                            'UNION', 'BROADWAY', 'EASTERN', 'QUAIL',
                            'MAIN STREET', 'FIRST STREET', 'SECOND STREET',
                            # State abbreviations
                            'IOWA', 'SOUTH DAKOTA', 'MINNESOTA', 'WISCONSIN',
                            'IA', 'SD', 'MN', 'WI',
                        ],
                        boost=15.0  # Strong boost for accurate route matching
                    )
                ],
                profanity_filter=False,  # Don't filter route-related terms
            )
            
            audio = speech_v1.RecognitionAudio(content=audio_data)
            response = self.client.recognize(config=config, audio=audio)
            
            if response.results and response.results[0].alternatives:
                transcript = response.results[0].alternatives[0].transcript
                confidence = response.results[0].alternatives[0].confidence
                print(f"[INFO] Transcription confidence: {confidence:.2%}\n")
                if confidence < 0.5:
                    print(f"[WARNING] Low confidence ({confidence:.2%}) - result may be inaccurate\n")
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
                model='latest_long',
                speech_contexts=[
                    speech_v1.SpeechContext(
                        phrases=[
                            # Route numbers - most critical
                            'I-29', 'I-35', 'I-90', 'I-80', 'I-70', 'I-480',
                            'US-75', 'US-59', 'US-18', 'US-69', 'US-20', 'US-30',
                            'IA-9', 'IA-4', 'IA-3', 'IA-27', 'IA-175',
                            'B-62', 'B62', 'A-10', 'A10',
                            # Directional suffixes
                            'NORTHBOUND', 'SOUTHBOUND', 'EASTBOUND', 'WESTBOUND',
                            'NB', 'SB', 'EB', 'WB', 'NORTH', 'SOUTH', 'EAST', 'WEST',
                            # Intersection markers
                            'INTERSECTION', 'AT INTERSECTION', 'MILEPOST', 'MP',
                            'STATE BORDER', 'JUNCTION', 'EXIT', 'MILE MARKER',
                            # Action commands
                            'START ON', 'START AT', 'END ON', 'END AT', 'END UP',
                            'CONTINUE', 'TURN', 'MERGE', 'TAKE',
                            'AT', 'IN', 'NEAR', 'TOWARDS',
                            # City and location names
                            'LYON', 'ROCK RAPIDS', 'SANBORN', 'EMMETSBURG', 
                            'HANCOCK', 'SIOUX CITY', 'SPENCER', 'ESTHERVILLE',
                            'CHEROKEE', 'STORM LAKE', 'TOLEDO', 'MAPLETON',
                            'WASHTA', 'DUNLAP', 'DENISON', 'CRAWFORD',
                            # Street names
                            'UNION', 'BROADWAY', 'EASTERN', 'QUAIL',
                            'MAIN STREET', 'FIRST STREET', 'SECOND STREET',
                            # State abbreviations
                            'IOWA', 'SOUTH DAKOTA', 'MINNESOTA', 'WISCONSIN',
                            'IA', 'SD', 'MN', 'WI',
                        ],
                        boost=15.0
                    )
                ],
                profanity_filter=False,
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
