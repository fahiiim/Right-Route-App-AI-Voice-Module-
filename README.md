# Right Route App - AI Voice Module

A professional speech-to-text module for capturing and parsing USA-based route instructions using **Google Cloud Speech-to-Text API** and **OpenAI GPT models**.

## Features

✅ **Real-time Audio Recording**
- Intelligent microphone input with voice activity detection
- Auto-stops after 10 seconds of silence
- Clear speech detection (RMS threshold filtering)
- Maximum 3-minute recording duration

✅ **Advanced Speech Processing**
- Aggressive noise reduction (95% prop_decrease)
- High-pass filter (300 Hz) - removes rumble and AC hum
- Low-pass filter (7 kHz) - removes hiss artifacts
- Frequency optimization for human speech (300-7000 Hz)

✅ **Accurate Transcription**
- Google Cloud Speech-to-Text with enhanced model
- Support for long-form audio (180 seconds)
- Route-specific speech context hints
- Fallback streaming recognition

✅ **Intelligent Route Parsing**
- OpenAI GPT-4o for STT error correction
- Automatic fixing of common speech recognition errors:
  - "IA 9" → "IA-9"
  - "san boom" → "SANBORN"
  - "coil av" → "QUAIL AVE"
  - Split words joining and formatting
- USA-specific highway and state recognition
- Proper punctuation and formatting

✅ **Structured Output**
```json
{
  "start_point": "START ON IA-9 EB AT A10 INTERSECTION (LYON) (STATE BORDER OF SOUTH DAKOTA)",
  "end_point": "END ON B62 WB AT QUAIL AVE INTERSECTION (HANCOCK) (IOWA)",
  "route_segments": ["US-75 SB", "IA-9 EB", "US-59 SB", "US-18 EB", "IA-4 SB", "IA-3 EB", "US-69 NB", "B62 WB"],
  "corrected_text": "Full corrected route instruction with proper formatting"
}
```

## Installation

### Prerequisites
- Python 3.8+
- Microphone access
- OpenAI API key
- Google Cloud service account credentials

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/fahiiim/Right-Route-App-AI-Voice-Module-.git
   cd Right-Route-App-AI-Voice-Module-
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env with your credentials
   nano .env  # or use your editor
   ```

5. **Add API Credentials**

   **OpenAI API Key:**
   - Get from: https://platform.openai.com/account/api-keys
   - Add to `.env`: `OPENAI_API_KEY=sk-...`

   **Google Cloud Credentials:**
   - Create service account: https://console.cloud.google.com/iam-admin/serviceaccounts
   - Download JSON key file
   - Option A: Set path in `.env`: `GOOGLE_CLOUD_CREDENTIALS=/path/to/key.json`
   - Option B: Set JSON content in `.env`: `GOOGLE_CLOUD_CREDENTIALS={"type":"service_account",...}`

## Usage

### Basic Usage
```bash
python stt_module.py
```

### Output
```
[RECORDING] Max 180s, auto-stop after 10s silence

Speak clearly... Background noise will be ignored.

[SILENCE DETECTED] Recording stopped

[RECORDING] Complete

[PROCESSING] Google Cloud STT...

[INFO] Used standard recognition (better for complex content)

[ROUTE EXTRACTION] Correcting STT errors and parsing with OpenAI...

[ROUTE EXTRACTION] Complete

[INFO] Corrected transcription:
Authorized Route: START ON IA-9 EB AT A10 INTERSECTION (LYON)(STATE BORDER OF SOUTH DAKOTA)...

============================================================
ROUTE INFORMATION (USA)
============================================================

START POINT: START ON IA-9 EB AT A10 INTERSECTION (LYON) (STATE BORDER OF SOUTH DAKOTA)
END POINT: END ON B62 WB AT QUAIL AVE INTERSECTION (HANCOCK) (IOWA)

ROUTE SEGMENTS (Sequential):
  1. US-75 SB
  2. IA-9 EB
  3. US-59 SB
  4. US-18 EB
  5. IA-4 SB
  6. IA-3 EB
  7. US-69 NB
  8. B62 WB

============================================================
```

## Architecture

### Module Structure

```
Right-Route-App-AI-Voice-Module/
├── stt_module.py          # Main STT recording and transcription module
├── config.py              # Google Cloud configuration
├── route_parser.py        # OpenAI route extraction and parsing
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variable template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

### Processing Pipeline

```
Microphone Audio
     ↓
[Audio Recording with Voice Detection]
     ↓
[Audio Preprocessing - Noise Reduction & Filtering]
     ↓
[Google Cloud STT Transcription]
     ↓
[OpenAI STT Error Correction & Route Parsing]
     ↓
[Structured Route JSON Output]
```

## Configuration

### Recording Parameters
- **Max Duration**: 180 seconds (3 minutes)
- **Silence Threshold**: 10 seconds (auto-stop)
- **Speech Threshold**: 500 RMS (high-quality speech detection)
- **Sample Rate**: 16000 Hz
- **Audio Format**: LINEAR16 (16-bit PCM)

### Audio Processing
- **Noise Reduction**: Aggressive (95% prop_decrease)
- **High-Pass Filter**: 300 Hz (removes rumble)
- **Low-Pass Filter**: 7 kHz (removes hiss)

### STT Configuration
- **Google Cloud Model**: video (optimized for long-form audio)
- **Enhanced Model**: Enabled (better accuracy)
- **Punctuation**: Automatic
- **OpenAI Model**: GPT-4o (best accuracy for route parsing)

## API Keys & Security

⚠️ **IMPORTANT SECURITY NOTES:**

1. **Never commit API keys** - Use `.env` files
2. **Use `.gitignore`** - Prevents accidental key leaks
3. **Rotate keys regularly** - If exposed, rotate immediately
4. **Use environment variables** - All keys loaded from `.env`
5. **Restrict API permissions** - Use minimal scopes needed

### If Keys Are Exposed

1. **Immediately revoke the keys:**
   - OpenAI: https://platform.openai.com/account/api-keys
   - Google Cloud: IAM console

2. **Generate new keys**

3. **Commit the .env file removal:**
   ```bash
   git rm --cached .env
   git commit -m "Remove exposed credentials"
   ```

## Troubleshooting

### API Key Issues
```
[ERROR] OPENAI_API_KEY environment variable not set
```
**Solution**: Add `OPENAI_API_KEY` to `.env` file

### Empty JSON Response
```
[ERROR] Route extraction failed: Expecting value: line 1 column 1
```
**Solution**: 
- Check API quota at https://platform.openai.com/account/billing/overview
- Verify API key is valid
- Test with: `python test_api.py`

### No Speech Detected
```
[ERROR] No speech detected. Please try again.
```
**Solution**:
- Speak clearly and directly into microphone
- Increase microphone volume
- Reduce background noise

### Google Cloud Authentication Error
```
[ERROR] credentials must be of type google.auth.credentials.Credentials
```
**Solution**:
- Verify `GOOGLE_CLOUD_CREDENTIALS` is set correctly
- Check service account JSON format
- Use absolute file path if using file-based credentials

## Testing

### Test API Connection
```bash
python test_api.py
```

This script tests:
- OpenAI API connectivity
- Available models
- Quota status
- Fallback mechanisms

## Performance Metrics

- **Recording Time**: 30-60 seconds typical (auto-stops)
- **Preprocessing Time**: 2-5 seconds
- **STT Processing**: 5-15 seconds (depends on audio length)
- **OpenAI Parsing**: 2-5 seconds
- **Total Time**: 10-35 seconds per route

## Supported Routes

- **Interstate Highways**: I-90, I-80, I-70, etc.
- **US Routes**: US-75, US-59, US-18, US-69, etc.
- **State Highways**: IA-9, IA-4, IA-3, B62, etc.
- **US States**: All 50 states supported
- **City/Intersection Format**: Natural language parsing

## Example Route Instruction

**Input (Spoken):**
> "Authorized Route: START ON IA-9 EB AT A10 INTERSECTION LYON STATE BORDER OF SOUTH DAKOTA, US-75 SB, IA-9 EB IN ROCK RAPIDS AT N UNION ST, US-59 SB, US-18 EB IN SANBORN AT EASTERN ST, IA-4 SB IN EMMETSBURG AT BROADWAY, IA-3 EB, US-69 NB, B62 WB HANCOCK, END ON B62 AT QUAIL AVE INTERSECTION HANCOCK"

**Output (Parsed):**
```json
{
  "start_point": "START ON IA-9 EB AT A10 INTERSECTION (LYON) (STATE BORDER OF SOUTH DAKOTA)",
  "end_point": "END ON B62 WB AT QUAIL AVE INTERSECTION (HANCOCK) (IOWA)",
  "route_segments": [
    "US-75 SB",
    "IA-9 EB",
    "US-59 SB",
    "US-18 EB",
    "IA-4 SB",
    "IA-3 EB",
    "US-69 NB",
    "B62 WB"
  ],
  "corrected_text": "Authorized Route: START ON IA-9 EB AT A10 INTERSECTION (LYON)(STATE BORDER OF SOUTH DAKOTA), US-75 SB, IA-9 EB(IN ROCK RAPIDS AT N UNION ST), US-59 SB, US-18 EB(IN SANBORN AT EASTERN ST), IA-4 SB(IN EMMETSBURG AT BROADWAY), IA-3 EB, US-69 NB, [B62 WB (HANCOCK), END ON B62 AT QUAIL AVE INTERSECTION (HANCOCK)]"
}
```

## Dependencies

- **sounddevice** - Microphone audio input
- **numpy** - Audio signal processing
- **google-cloud-speech** - Google Cloud STT API
- **openai** - OpenAI API client
- **noisereduce** - Audio noise reduction
- **scipy** - Signal filtering (high-pass, low-pass)
- **google-auth** - Authentication

See `requirements.txt` for versions.

## License

This project is proprietary software. Unauthorized copying or distribution is prohibited.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review the error messages in detail
3. Check API quotas and limits
4. Contact: [your email/contact info]

## Changelog

### v1.0.0 (2025-12-12)
- Initial release
- Google Cloud STT integration
- OpenAI route parsing
- Audio preprocessing with noise reduction
- Environment variable security
