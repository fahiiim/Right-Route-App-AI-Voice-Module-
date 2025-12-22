"""
OpenAI API Configuration for Route Extraction
Handles parsing and structuring route instructions
"""

import os
import re
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with API key from environment
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    raise ValueError(
        "OPENAI_API_KEY environment variable not set.\n"
        "Please set your OpenAI API key before running this module."
    )

client = OpenAI(api_key=api_key)

# State Abbreviations to Full Names Mapping
STATE_ABBREVIATIONS = {
    'AL': 'Alabama',
    'AK': 'Alaska',
    'AZ': 'Arizona',
    'AR': 'Arkansas',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'HI': 'Hawaii',
    'ID': 'Idaho',
    'IL': 'Illinois',
    'IN': 'Indiana',
    'IA': 'Iowa',
    'KS': 'Kansas',
    'KY': 'Kentucky',
    'LA': 'Louisiana',
    'ME': 'Maine',
    'MD': 'Maryland',
    'MA': 'Massachusetts',
    'MI': 'Michigan',
    'MN': 'Minnesota',
    'MS': 'Mississippi',
    'MO': 'Missouri',
    'MT': 'Montana',
    'NE': 'Nebraska',
    'NV': 'Nevada',
    'NH': 'New Hampshire',
    'NJ': 'New Jersey',
    'NM': 'New Mexico',
    'NY': 'New York',
    'NC': 'North Carolina',
    'ND': 'North Dakota',
    'OH': 'Ohio',
    'OK': 'Oklahoma',
    'OR': 'Oregon',
    'PA': 'Pennsylvania',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VT': 'Vermont',
    'VA': 'Virginia',
    'WA': 'Washington',
    'WV': 'West Virginia',
    'WI': 'Wisconsin',
    'WY': 'Wyoming'
}

# Route Direction Abbreviations to Full Names Mapping
DIRECTION_ABBREVIATIONS = {
    'NB': 'Northbound',
    'SB': 'Southbound',
    'EB': 'Eastbound',
    'WB': 'Westbound'
}

# Basic Direction Abbreviations
BASIC_DIRECTIONS = {
    'N': 'North',
    'S': 'South',
    'E': 'East',
    'W': 'West'
}

# System prompt for route extraction with advanced prompt engineering
ROUTE_EXTRACTION_PROMPT = """
You are an expert US route instruction parser and advanced speech-to-text error corrector. Your task is to:
1. Aggressively correct ALL STT errors in transcribed route instructions
2. Properly format route data with correct punctuation and capitalization
3. Extract and structure route information accurately with FULL start and end locations
4. CRITICALLY: Detect when the input contains NO actual route instructions and return an error response

CRITICAL CONTEXT:
- This application is exclusively for USA-based routes and highways
- You work with US Interstate highways (I-X), US routes (US-X), State highways (XX-X), County roads (B-X)
- Common US states: Iowa (IA), South Dakota (SD), Minnesota (MN), Wisconsin (WI), Illinois (IL), etc.
- Cities mentioned are always US cities
- Route segments MUST include start and end locations with full intersection details
- Intersections use proper formatting: "AT [LOCATION] INTERSECTION" or "[ROUTE] AT [INTERSECTION]"
- If the transcribed text contains NO route instructions, road names, or route markers, return an error JSON immediately

AGGRESSIVE STT ERROR CORRECTION - FIX THESE PATTERNS:
ROUTE NUMBER ERRORS:
- "I 29" or "eye 29" or "I-29" variations → "I-29"
- "US 75" or "you ess 75" → "US-75"  
- "IA 9" or "in 9" or "ia-9" → "IA-9"
- "B 62" or "bee 62" → "B62"
- "A 10" or "ay 10" → "A10"
- Split: "I A 4" or "I A4" → "IA-4"
- "169" or "one six nine" in context → "US-69"

DIRECTIONAL ERRORS:
- "S B" or "south bound" → "SB"
- "N B" or "north bound" → "NB"
- "E B" or "east bound" → "EB"
- "W B" or "west bound" → "WB"

CITY/LOCATION ERRORS:
- "lien" or "lyon" → "LYON"
- "rock rapids" → "ROCK RAPIDS"
- "san born" or "san boom" → "SANBORN"
- "emmetsburg" or variations → "EMMETSBURG"
- "hancock" → "HANCOCK"

STREET/LOCATION ERRORS:
- "any union" or "n union" → "N UNION ST" or "UNION STREET"
- "easter" or "eastern" → "EASTERN"
- "quail" or "quale" → "QUAIL"

MARKER ERRORS:
- "mile post" or "MP" variations → "MILEPOST" or "MP"
- "intersection" variations → "INTERSECTION"

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
3. Route segments in sequential order WITH the start and end locations included as the first and last items

RESPONSE FORMAT - YOU MUST RETURN VALID JSON ONLY:
You must respond with ONLY a valid JSON object with no markdown, code blocks, or additional text. The JSON must be on a single line or properly formatted.

If input contains NO route data, return:
{"error": "No route instructions detected in transcription", "has_routes": false, "input_was": "exact transcribed text here"}

Example valid response for route data:
{"start_location": "IA-9 EB AT A10 INTERSECTION (LYON), South Dakota", "end_location": "B62 AT QUAIL AVE INTERSECTION (HANCOCK), South Dakota", "route_segments": ["IA-9 EB AT A10 INTERSECTION (LYON)", "US-75 SB", "IA-9 EB (in Rock Rapids at N Union St)", "US-59 SB", "US-18 EB (in Sanborn at Eastern St)", "IA-4 SB (in Emmetsburg at Broadway)", "IA-3 EB", "US-69 NB", "B62 WB (Hancock)", "B62 AT QUAIL AVE INTERSECTION (HANCOCK)"], "has_routes": true, "corrected_text": "Authorized Route: START ON IA-9 EB AT A10 INTERSECTION (LYON) SOUTH DAKOTA, US-75 SB, IA-9 EB (IN ROCK RAPIDS AT N UNION ST), US-59 SB, US-18 EB (IN SANBORN AT EASTERN ST), IA-4 SB (IN EMMETSBURG AT BROADWAY), IA-3 EB, US-69 NB, B62 WB (HANCOCK), END ON B62 AT QUAIL AVE INTERSECTION (HANCOCK) SOUTH DAKOTA"}

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
        print(f"[DEBUG] Input text being sent to OpenAI: {transcribed_text}\n")
        
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
            temperature=0.3,  # Slightly higher temperature to avoid repetition bias
            max_tokens=800
        )
        
        response_text = response.choices[0].message.content
        print(f"[DEBUG] Raw OpenAI response: {response_text}\n")
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
        
        # Check if OpenAI detected no routes
        if route_data.get('error'):
            print(f"[WARNING] {route_data.get('error')}\n")
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
    Format the extracted route data for display with expanded abbreviations
    
    Args:
        route_data: Dictionary with structured route information
        
    Returns:
        str: Formatted route information with full names instead of abbreviations
    """
    if not route_data:
        return "Unable to parse route information"
    
    output = "\n" + "🗺️  Route Information:\n"
    output += "-"*60 + "\n"
    
    # Create JSON-like output with proper formatting
    output += "{\n"
    start_loc = route_data.get("start_location", "N/A")
    end_loc = route_data.get("end_location", "N/A")
    
    # Expand abbreviations in locations
    start_loc_expanded = expand_abbreviations(start_loc)
    end_loc_expanded = expand_abbreviations(end_loc)
    
    output += f'  "start_location": "{start_loc_expanded}",\n'
    output += f'  "end_location": "{end_loc_expanded}",\n'
    
    output += '  "route_segments": [\n'
    segments = route_data.get('route_segments', [])
    for i, segment in enumerate(segments):
        expanded_segment = expand_abbreviations(segment)
        if i < len(segments) - 1:
            output += f'    "{expanded_segment}",\n'
        else:
            output += f'    "{expanded_segment}"\n'
    output += "  ]\n"
    output += "}\n"
    
    return output


def expand_abbreviations(text):
    """
    Expand state, direction, and basic direction abbreviations in route text
    
    Args:
        text: String containing route information with abbreviations
        
    Returns:
        str: String with all abbreviations expanded to full names
    """
    if not text:
        return text
    
    result = text
    
    # Replace state abbreviations (e.g., "IA" -> "Iowa")
    # Use word boundaries to avoid partial matches
    for abbr, full_name in STATE_ABBREVIATIONS.items():
        # Match abbreviation as a standalone word (not part of a larger word)
        pattern = r'\b' + abbr + r'\b'
        result = re.sub(pattern, full_name, result, flags=re.IGNORECASE)
    
    # Replace direction abbreviations (e.g., "NB" -> "Northbound")
    for abbr, full_name in DIRECTION_ABBREVIATIONS.items():
        pattern = r'\b' + abbr + r'\b'
        result = re.sub(pattern, full_name, result, flags=re.IGNORECASE)
    
    # Replace basic direction abbreviations (e.g., "N" -> "North")
    # Need to be careful not to match single letters in other contexts
    for abbr, full_name in BASIC_DIRECTIONS.items():
        # Match single direction letters that are preceded and followed by spaces or specific characters
        pattern = r'\b' + abbr + r'(?=\s|,|$)'
        result = re.sub(pattern, full_name, result, flags=re.IGNORECASE)
    
    return result
