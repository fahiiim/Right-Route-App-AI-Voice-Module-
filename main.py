"""
CLI Application for Voice-Based Route Module
Terminal-based testing and development
"""

from stt_module import SpeechToTextModule
from route_parser import extract_routes, format_route_output
import json


def print_menu():
    """Display main menu"""
    print("\n" + "="*60)
    print("Voice Route Module - Terminal CLI")
    print("="*60)
    print("1. Record audio and extract route")
    print("2. Test with sample text")
    print("3. Enter custom text for route extraction")
    print("4. Exit")
    print("="*60)


def process_voice():
    """Process audio from microphone"""
    print("\n[STARTING] Voice recording...")
    stt = SpeechToTextModule()
    
    try:
        # Record audio
        audio_data = stt.record_audio()
        
        if not audio_data:
            print("[ERROR] No audio recorded. Please try again.")
            return
        
        # Transcribe audio
        print("\n[PROCESSING] Transcribing audio...")
        transcribed_text = stt.transcribe_audio(audio_data)
        
        if not transcribed_text:
            print("[ERROR] Could not transcribe audio.")
            return
        
        print(f"\n[TRANSCRIBED] {transcribed_text}")
        
        # Extract routes
        print("\n[EXTRACTING] Route information...")
        route_data = extract_routes(transcribed_text)
        
        if route_data and route_data.get('error'):
            print(f"[ERROR] {route_data.get('error')}")
        elif route_data:
            print(f"\n[SUCCESS] Route extracted:")
            print(format_route_output(route_data))
        else:
            print("[ERROR] Failed to extract route data")
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")


def test_sample_text():
    """Test with predefined sample text"""
    sample_texts = [
        "START ON IA-9 EB AT A10 INTERSECTION LYON IOWA, US-75 SB, IA-9 EB, US-59 SB, END ON B62 WB AT QUAIL AVE INTERSECTION HANCOCK IOWA",
        "Authorized Route: START ON US-75 SB, travel through IA-9 EB, US-59 SB, US-18 EB, IA-4 SB, IA-3 EB, END ON B62 WB"
    ]
    
    print("\n[AVAILABLE SAMPLES]")
    for i, text in enumerate(sample_texts, 1):
        print(f"{i}. {text}")
    
    try:
        choice = int(input("\nSelect sample (1-2): "))
        if 1 <= choice <= len(sample_texts):
            test_text = sample_texts[choice - 1]
            print(f"\n[TESTING] Text: {test_text}")
            print("\n[EXTRACTING] Route information...")
            route_data = extract_routes(test_text)
            
            if route_data and route_data.get('error'):
                print(f"[ERROR] {route_data.get('error')}")
            elif route_data:
                print(f"\n[SUCCESS] Route extracted:")
                print(format_route_output(route_data))
            else:
                print("[ERROR] Failed to extract route data")
        else:
            print("[ERROR] Invalid selection")
    except ValueError:
        print("[ERROR] Invalid input")


def custom_text_input():
    """Enter custom text for route extraction"""
    print("\nEnter route instruction text (or 'cancel' to go back):")
    user_text = input("> ").strip()
    
    if user_text.lower() == 'cancel':
        return
    
    if not user_text:
        print("[ERROR] Text cannot be empty")
        return
    
    print(f"\n[PROCESSING] Text: {user_text}")
    route_data = extract_routes(user_text)
    
    if route_data and route_data.get('error'):
        print(f"[ERROR] {route_data.get('error')}")
    elif route_data:
        print(f"\n[SUCCESS] Route extracted:")
        print(format_route_output(route_data))
    else:
        print("[ERROR] Failed to extract route data")


def main():
    """Main CLI loop"""
    print("\nVoice Route Module - CLI Mode")
    print("Ready for testing...")
    
    while True:
        print_menu()
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            process_voice()
        elif choice == '2':
            test_sample_text()
        elif choice == '3':
            custom_text_input()
        elif choice == '4':
            print("\n[EXIT] Goodbye!")
            break
        else:
            print("[ERROR] Invalid option. Please select 1-4")


if __name__ == "__main__":
    main()
