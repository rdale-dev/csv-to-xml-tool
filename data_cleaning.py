  
"""
Enhanced data cleaning and formatting utilities for Salesforce CSV to XML conversion.
This module contains functions for cleaning and standardizing Salesforce data formats.
"""
import re
from datetime import datetime
from config import MAX_FIELD_LENGTHS, MIN_COUNSELING_DATE

def standardize_state_name(state):
    """
    Standardizes state codes to ensure they match the required format in XSD.
    Converts state abbreviations to full state names and handles various formats.
    
    Args:
        state: State name or code
        
    Returns:
        Standardized state name
    """
    if not state or str(state).strip() == "" or str(state).lower() == "nan":
        return ""  # Return empty string if state is empty
    
    state_str = str(state).strip()
    
    # State code to full name mapping
    state_map = {
        "AL": "Alabama",
        "AK": "Alaska",
        "AZ": "Arizona",
        "AR": "Arkansas",
        "CA": "California",
        "CO": "Colorado",
        "CT": "Connecticut",
        "DE": "Delaware",
        "FL": "Florida",
        "GA": "Georgia",
        "HI": "Hawaii",
        "ID": "Idaho",
        "IL": "Illinois",
        "IN": "Indiana",
        "IA": "Iowa",
        "KS": "Kansas",
        "KY": "Kentucky",
        "LA": "Louisiana",
        "ME": "Maine",
        "MD": "Maryland",
        "MA": "Massachusetts",
        "MI": "Michigan",
        "MN": "Minnesota",
        "MS": "Mississippi",
        "MO": "Missouri",
        "MT": "Montana",
        "NE": "Nebraska",
        "NV": "Nevada",
        "NH": "New Hampshire",
        "NJ": "New Jersey",
        "NM": "New Mexico",
        "NY": "New York",
        "NC": "North Carolina",
        "ND": "North Dakota",
        "OH": "Ohio",
        "OK": "Oklahoma",
        "OR": "Oregon",
        "PA": "Pennsylvania",
        "RI": "Rhode Island",
        "SC": "South Carolina",
        "SD": "South Dakota",
        "TN": "Tennessee",
        "TX": "Texas",
        "UT": "Utah",
        "VT": "Vermont",
        "VA": "Virginia",
        "WA": "Washington",
        "WV": "West Virginia",
        "WI": "Wisconsin",
        "WY": "Wyoming",
        "DC": "District of Columbia"
    }
    
    # Case insensitive check for state codes
    for code, name in state_map.items():
        if state_str.upper() == code:
            return name
    
    # Already a full state name or unrecognized value - do a case-insensitive check
    for name in state_map.values():
        if state_str.lower() == name.lower():
            return name  # Return the proper case version
    
    # If we couldn't match it, return the original value
    return state_str

def standardize_country_code(country):
    """
    Standardizes country codes to ensure they match the required format in XSD.
    Handles various forms of country codes including "US", "USA", etc.
    
    Args:
        country: Country name or code
        
    Returns:
        Standardized country name
    """
    if not country or str(country).strip() == "" or str(country).lower() == "nan":
        return "United States"  # Default to United States if empty
    
    country_str = str(country).strip()
    
    # Convert to uppercase for consistent comparison
    country_upper = country_str.upper()
    
    # Hard-coded conversion for US variants with case-insensitive matching
    us_variants = ["US", "USA", "U.S.", "U.S.A.", "UNITED STATES"]
    if country_upper in us_variants:
        return "United States"
        
    # Common variations to standardize (case-insensitive)
    country_map = {
        "USA": "United States",
        "U.S.": "United States",
        "U.S.A.": "United States",
        "UNITED STATES OF AMERICA": "United States",
        "AMERICA": "United States",
        "CA": "Canada",
        "CAN": "Canada",
        "MX": "Mexico",
        "MEX": "Mexico",
        "UK": "United Kingdom",
        "GB": "United Kingdom",
        "GBR": "United Kingdom",
        "GREAT BRITAIN": "United Kingdom",
        "ENGLAND": "United Kingdom"
    }
    
    # Try exact match first (case-insensitive)
    for code, name in country_map.items():
        if country_upper == code:
            return name
    
    # If we couldn't match it, return the original value
    return country_str

def clean_phone_number(phone):
    """
    Removes all non-numeric characters from a phone number.
    Returns empty string if phone is None or empty.
    
    Examples:
        "(123) 456-7890" -> "1234567890"
        "123.456.7890" -> "1234567890"
        "+1 (123) 456-7890" -> "11234567890"
    """
    if not phone or str(phone).strip() == "" or str(phone).lower() == "nan":
        return ""
        
    return ''.join(char for char in str(phone) if char.isdigit())

def format_date(date_str):
    """
    Converts date from various formats to YYYY-MM-DD format.
    Returns empty string if date_str is empty or None.
    
    Handles Salesforce date formats:
        - MM/DD/YYYY
        - YYYY-MM-DD
        - MM-DD-YYYY
    """
    if not date_str or str(date_str).strip() == "" or str(date_str).lower() == "nan":
        return ""
    
    try:
        # Try different date formats
        date_str = str(date_str).strip()
        
        # Check if it's already in YYYY-MM-DD format
        if re.match(r'\d{4}-\d{1,2}-\d{1,2}', date_str):
            year, month, day = date_str.split('-')
            month = month.zfill(2)
            day = day.zfill(2)
            return f"{year}-{month}-{day}"
        
        # Try MM/DD/YYYY format
        elif '/' in date_str:
            month, day, year = date_str.split('/')
            month = month.zfill(2)
            day = day.zfill(2)
            return f"{year}-{month}-{day}"
        
        # Try MM-DD-YYYY format
        elif '-' in date_str:
            month, day, year = date_str.split('-')
            month = month.zfill(2)
            day = day.zfill(2)
            return f"{year}-{month}-{day}"
            
        # If nothing else works, return as is
        return date_str
    except (ValueError, AttributeError):
        return ""

def validate_counseling_date(date_str):
    """
    Validates that the counseling date is not before MIN_COUNSELING_DATE.
    
    Args:
        date_str: A date string in YYYY-MM-DD format
        
    Returns:
        Boolean indicating if the date is valid
    """
    if not date_str:
        return True
    
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        min_date = datetime.strptime(MIN_COUNSELING_DATE, "%Y-%m-%d")
        return date_obj >= min_date
    except ValueError:
        return False

def clean_whitespace(text):
    """
    Cleans excess whitespace from text while preserving normal spacing between words and sentences.
    - Replaces multiple spaces with a single space
    - Removes leading/trailing whitespace
    - Preserves single newlines but removes extras
    - Handles Salesforce-specific patterns
    """
    if not text or str(text).strip() == "" or str(text).lower() == "nan":
        return ""
        
    # Convert to string explicitly
    text = str(text)
    
    # Split on newlines and handle each line
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Remove leading/trailing whitespace from each line
        line = line.strip()
        # Replace multiple spaces with single space
        line = ' '.join(line.split())
        # Remove Salesforce-specific artifacts
        line = re.sub(r'\[\w+\]:', '', line)  # Removes things like [User]: 
        if line:  # Only add non-empty lines
            cleaned_lines.append(line)
    
    # Join with single newlines
    return '\n'.join(cleaned_lines)

def map_gender_to_sex(gender_value):
    """
    Maps various gender values to just 'Female' or 'Male' per XSD requirements.
    Returns empty string if no match or missing.
    """
    if not gender_value or str(gender_value).strip() == "" or str(gender_value).lower() == "nan":
        return ""
    
    gender_str = str(gender_value).lower()
    
    if "female" in gender_str:
        return "Female"
    elif "male" in gender_str and not "female" in gender_str:  # Handle edge case for "Female" containing "male"
        return "Male"
    
    # Return empty string for any other values like "Non-binary", "Prefer not to say", etc.
    return ""

def split_multi_value(value, delimiter=";"):
    """
    Splits multi-value fields with the specified delimiter.
    Returns an empty list if the value is empty or None.
    """
    if not value or str(value).strip() == "" or str(value).lower() == "nan":
        return []
    
    return [item.strip() for item in str(value).split(delimiter) if item.strip()]

def clean_numeric(value):
    """
    Cleans numeric values to ensure they're valid.
    Returns empty string if invalid or None.
    """
    if not value or str(value).strip() == "" or str(value).lower() == "nan":
        return ""
    
    try:
        # Try to convert to float and then string (removes redundant .0)
        float_val = float(value)
        # If it's a whole number, return it as an integer
        if float_val.is_integer():
            return str(int(float_val))
        # Otherwise return as float
        return str(float_val)
    except (ValueError, TypeError):
        return ""

def clean_percentage(value):
    """
    Cleans percentage values ensuring they're valid.
    Returns a number between 0 and 100.
    """
    if not value or str(value).strip() == "" or str(value).lower() == "nan":
        return "0"
    
    try:
        float_val = float(value)
        # Ensure it's between 0 and 100
        float_val = max(0, min(100, float_val))
        return str(float_val)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid percentage value: {value}")

def truncate_counselor_notes(notes, max_length=MAX_FIELD_LENGTHS["CounselorNotes"]):
    """
    Cleans counselor notes and ensures they don't exceed the maximum length.
    If notes exceed max_length, they are truncated at a sentence or word boundary.
    
    Args:
        notes: The counselor notes text
        max_length: Maximum allowed length (default from config)
        
    Returns:
        Cleaned and truncated notes
    """
    # First clean the whitespace
    cleaned_notes = clean_whitespace(notes)
    
    # If already within limit, return as is
    if len(cleaned_notes) <= max_length:
        return cleaned_notes
    
    # Try to truncate at a sentence boundary
    truncated = cleaned_notes[:max_length]
    
    # Look for last sentence boundary within the limit
    sentence_boundaries = ['.', '!', '?', '\n']
    last_boundary_pos = -1
    
    for boundary in sentence_boundaries:
        pos = truncated.rfind(boundary)
        if pos > last_boundary_pos:
            last_boundary_pos = pos
    
    # If found a sentence boundary, truncate there
    if last_boundary_pos > 0:
        return cleaned_notes[:last_boundary_pos + 1]
    
    # Otherwise try to truncate at a word boundary
    last_space = truncated.rfind(' ')
    if last_space > 0:
        return cleaned_notes[:last_space]
    
    # If all else fails, just truncate at max_length
    return truncated