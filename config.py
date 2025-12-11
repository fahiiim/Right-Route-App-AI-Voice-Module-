"""
Google Cloud STT API Configuration
Secure credentials and settings for Google Cloud Speech-to-Text API
"""

import os
import json
from google.cloud import speech_v1
from google.oauth2 import service_account

# Load Google Cloud credentials from environment variable or file
def get_google_credentials():
    """Load Google Cloud credentials securely from environment"""
    creds_json = os.getenv('GOOGLE_CLOUD_CREDENTIALS')
    
    if not creds_json:
        raise ValueError(
            "GOOGLE_CLOUD_CREDENTIALS environment variable not set.\n"
            "Please set it with your service account JSON content or path."
        )
    
    # Try to parse as JSON first, then as file path
    try:
        creds_dict = json.loads(creds_json)
    except json.JSONDecodeError:
        # Assume it's a file path
        with open(creds_json, 'r') as f:
            creds_dict = json.load(f)
    
    return creds_dict


def get_speech_client():
    """Initialize and return Google Cloud Speech client with credentials"""
    creds_dict = get_google_credentials()
    credentials = service_account.Credentials.from_service_account_info(creds_dict)
    return speech_v1.SpeechClient(credentials=credentials)


# STT Configuration optimized for route instructions
STT_CONFIG = {
    'language_code': 'en-US',
    'sample_rate_hertz': 16000,
    'audio_channel_count': 1,
    'encoding': speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
    'enable_automatic_punctuation': True,
    'use_enhanced': True,  # Enhanced model for better accuracy with complex text
}
