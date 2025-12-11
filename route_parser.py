"""
OpenAI API Configuration for Route Extraction
Handles parsing and structuring route instructions
"""

import os
from openai import OpenAI

# Initialize OpenAI client with API key from environment
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    raise ValueError(
        "OPENAI_API_KEY environment variable not set.\n"
        "Please set your OpenAI API key before running this module."
    )

client = OpenAI(api_key=api_key)

# System prompt for route extraction with advanced prompt engineering
ROUTE_EXTRACTION_PROMPT = """
You are an expert US route instruction parser and speech-to-text error corrector. Your task is to:
1. Correct common STT errors in transcribed route instructions
2. Properly format route data with correct punctuation and capitalization
3. Extract and structure route information accurately

CRITICAL CONTEXT:
- This application is exclusively for USA-based routes and highways
- You work with US Interstate highways (I-X), US routes (US-X), State highways (XX-X)
- Common US states: Iowa (IA), South Dakota (SD), Minnesota (MN), Wisconsin (WI), Illinois (IL), etc.
- Cities mentioned are always US cities
- Intersections use proper formatting: "AT [LOCATION] INTERSECTION"

COMMON STT ERRORS TO CORRECT:
- "IA 9" or "in 9" or "ia9" → "IA-9"
- "EB", "WB", "NB", "SB" (Eastbound, Westbound, Northbound, Southbound) - keep as-is
- "US 75" → "US-75"
- "at any union" → "AT N UNION" or "AT UNION"
- "san boom" or "san bond" → "SANBORN"
- "coil av" or "quail ave" → "QUAIL AVE"
- "wing" → "WB" (Westbound)
- "lien" → "LYON"
- Split words should be joined: "I A4" → "IA-4"
- Single "169" → "US-69"
- State abbreviations in parentheses like "(LYON)" → "(LYON)"

FORMATTING RULES:
- Use proper punctuation: commas between segments, parentheses for cities/states
- Format: "START ON [ROUTE] AT [INTERSECTION] ([CITY])([STATE]), [ROUTE], [ROUTE]..."
- Always include state abbreviations (SD, IA, MN, etc.)
- Capitalize cities and state names
- Use hyphens in route numbers: IA-9, US-75, B62

EXTRACTION TASK:
From the corrected transcription, extract:
1. Start location/intersection with city and state
2. End location/intersection with city and state
3. Route segments in sequential order with proper formatting

RESPONSE FORMAT - YOU MUST RETURN VALID JSON ONLY:
You must respond with ONLY a valid JSON object with no markdown, code blocks, or additional text. The JSON must be on a single line or properly formatted.

Example valid response:
{"start_point": "START ON IA-9 EB AT A10 INTERSECTION (LYON) (STATE BORDER OF SOUTH DAKOTA)", "end_point": "END ON B62 WB AT QUAIL AVE INTERSECTION (HANCOCK) (IOWA)", "route_segments": ["US-75 SB", "IA-9 EB", "US-59 SB", "US-18 EB", "IA-4 SB", "IA-3 EB", "US-69 NB", "B62 WB"], "corrected_text": "Authorized Route: START ON IA-9 EB AT A10 INTERSECTION (LYON)(STATE BORDER OF SOUTH DAKOTA), US-75 SB, IA-9 EB(IN ROCK RAPIDS AT N UNION ST), US-59 SB, US-18 EB(IN SANBORN AT EASTERN ST), IA-4 SB(IN EMMETSBURG AT BROADWAY), IA-3 EB, US-69 NB, [B62 WB (HANCOCK), END ON B62 AT QUAIL AVE INTERSECTION (HANCOCK)]"}

Be precise. Extract EXACTLY what is mentioned. Do not add or assume information.
Ensure all route numbers have hyphens (IA-9, US-75, B62).
Ensure all directions are properly formatted (SB, EB, NB, WB).
Ensure all punctuation is correct and readable.
Return ONLY valid JSON with no additional text.
"""


def extract_routes(transcribed_text):
    """
    Use OpenAI to correct STT errors and extract structured route information
    
    Args:
        transcribed_text: Raw transcribed text from STT
        
    Returns:
        dict: Structured route information with corrections or None if parsing fails
    """
    try:
        print("[ROUTE EXTRACTION] Correcting STT errors and parsing with OpenAI...\n")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": ROUTE_EXTRACTION_PROMPT
                },
                {
                    "role": "user",
                    "content": f"Correct and parse this route instruction transcription: {transcribed_text}"
                }
            ],
            temperature=0.2,  # Very low temperature for consistent, strict parsing
            max_tokens=800
        )
        
        response_text = response.choices[0].message.content
        print("[ROUTE EXTRACTION] Complete\n")
        
        # Check if response is empty
        if not response_text or response_text.strip() == '':
            print("[ERROR] OpenAI returned empty response\n")
            print("[INFO] Possible causes:\n")
            print("  - API key expired or invalid\n")
            print("  - Account out of credits\n")
            print("  - Model 'gpt-4o' not available\n")
            return None
        
        # Parse JSON response
        import json
        try:
            route_data = json.loads(response_text)
        except json.JSONDecodeError as je:
            print(f"[ERROR] Invalid JSON from OpenAI: {str(je)}\n")
            print(f"[DEBUG] Response was: {response_text[:200]}\n")
            return None
        
        # Display corrected text for verification
        if route_data.get('corrected_text'):
            print("[INFO] Corrected transcription:")
            print(f"{route_data.get('corrected_text')}\n")
        
        return route_data
        
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Route extraction failed: {error_msg}\n")
        
        # Check for specific API errors
        if 'invalid_api_key' in error_msg.lower():
            print("[CRITICAL] Invalid or expired OpenAI API key\n")
        elif 'insufficient_quota' in error_msg.lower():
            print("[CRITICAL] OpenAI account has insufficient quota (out of credits)\n")
        elif 'model_not_found' in error_msg.lower():
            print("[INFO] GPT-4o model not available. Trying GPT-3.5-turbo...\n")
            return extract_routes_fallback(transcribed_text)
        
        return None


def extract_routes_fallback(transcribed_text):
    """
    Fallback to GPT-3.5-turbo if GPT-4o is not available
    """
    try:
        print("[FALLBACK] Using GPT-3.5-turbo...\n")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": ROUTE_EXTRACTION_PROMPT
                },
                {
                    "role": "user",
                    "content": f"Correct and parse this route instruction transcription: {transcribed_text}"
                }
            ],
            temperature=0.2,
            max_tokens=800
        )
        
        response_text = response.choices[0].message.content
        import json
        route_data = json.loads(response_text)
        
        if route_data.get('corrected_text'):
            print("[INFO] Corrected transcription:")
            print(f"{route_data.get('corrected_text')}\n")
        
        return route_data
        
    except Exception as e:
        print(f"[ERROR] Fallback also failed: {str(e)}\n")
        return None


def format_route_output(route_data):
    """
    Format the extracted route data for display
    
    Args:
        route_data: Dictionary with structured route information
        
    Returns:
        str: Formatted route information
    """
    if not route_data:
        return "Unable to parse route information"
    
    output = "\n" + "="*70 + "\n"
    output += "ROUTE INFORMATION (USA)\n"
    output += "="*70 + "\n\n"
    
    output += f"START POINT: {route_data.get('start_point', 'N/A')}\n"
    output += f"END POINT: {route_data.get('end_point', 'N/A')}\n\n"
    
    output += "ROUTE SEGMENTS (Sequential):\n"
    segments = route_data.get('route_segments', [])
    for i, segment in enumerate(segments, 1):
        output += f"  {i}. {segment}\n"
    
    output += "\n" + "="*70 + "\n"
    
    return output
