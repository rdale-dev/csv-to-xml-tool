"""
Data validation module for CSV to XML conversion.
This module contains functions for validating data before XML conversion.
"""

from data_cleaning import (
    clean_phone_number, format_date, clean_whitespace, 
    validate_counseling_date, map_gender_to_sex, clean_numeric, 
    clean_percentage, standardize_country_code
)
from config import ValidationCategory as VC
from logging_util import logger
from validation_report import validator

def validate_record(row, row_index, record_id):
    """
    Validates a record and tracks any validation issues.
    
    Args:
        row: Dictionary of field values
        row_index: Index of the row in the CSV
        record_id: ID to use for the record
    
    Returns:
        Boolean indicating if the record passed all required validations
    """
    record_valid = True
    
    # Check required fields
    if not record_id:
        logger.error(f"Missing Contact ID for row {row_index}")
        validator.add_issue(
            f"Row_{row_index}", "error", VC.MISSING_REQUIRED, 
            "Contact ID", "Missing Contact ID (required field)"
        )
        record_valid = False
    
    # Validate name fields (recommended but not strictly required)
    last_name = row.get('Last Name', '')
    if not last_name:
        validator.add_issue(
            record_id, "warning", VC.MISSING_FIELD, 
            "Last Name", "Missing Last Name"
        )
    
    first_name = row.get('First Name', '')
    if not first_name:
        validator.add_issue(
            record_id, "warning", VC.MISSING_FIELD, 
            "First Name", "Missing First Name"
        )
    
    # Validate phone number
    phone = row.get('Contact: Phone', '')
    clean_phone = clean_phone_number(phone)
    if phone and not clean_phone:
        validator.add_issue(
            record_id, "warning", VC.INVALID_FORMAT, 
            "Phone", f"Invalid phone number format: {phone}"
        )
    
    # Validate email
    email = row.get('Email', '')
    if email and '@' not in email:
        validator.add_issue(
            record_id, "warning", VC.INVALID_FORMAT, 
            "Email", f"Invalid email format: {email}"
        )
    
    # Validate ZIP code format
    zip_code = row.get('Mailing Zip/Postal Code', '')
    if zip_code and not str(zip_code).strip().isdigit():
        validator.add_issue(
            record_id, "warning", VC.INVALID_FORMAT, 
            "ZipCode", f"Non-numeric ZIP code: {zip_code}"
        )
    
    # Validate country code
    country = row.get('Mailing Country', 'US')
    standardized = standardize_country_code(country)
    if standardized != country:
        validator.add_issue(
            record_id, "info", VC.STANDARDIZED_VALUE, 
            "Country", f"Standardized country: '{country}' -> '{standardized}'"
        )
    
    # Validate signature date
    signature_date = row.get('Client Signature - Date', '')
    if signature_date:
        formatted_date = format_date(signature_date)
        if not formatted_date:
            validator.add_issue(
                record_id, "warning", VC.INVALID_FORMAT, 
                "Signature Date", f"Invalid date format: {signature_date}"
            )
    
    # Validate race information
    race = row.get('Race', '')
    if not race:
        validator.add_issue(
            record_id, "warning", VC.MISSING_FIELD, 
            "Race", "Missing Race information"
        )
    
    # Validate female ownership percentage
    female_ownership = row.get('Business Ownership - % Female', '')
    if female_ownership:
        try:
            female_pct = clean_percentage(female_ownership)
        except ValueError:
            validator.add_issue(
                record_id, "warning", VC.INVALID_FORMAT, 
                "Business Ownership - % Female", f"Invalid percentage: {female_ownership}"
            )
    
    # Validate counseling date
    counseling_date = row.get('Date', '')
    if counseling_date:
        formatted_date = format_date(counseling_date)
        if not formatted_date:
            validator.add_issue(
                record_id, "warning", VC.INVALID_FORMAT, 
                "Date Counseled", f"Invalid date format: {counseling_date}"
            )
        elif not validate_counseling_date(formatted_date):
            validator.add_issue(
                record_id, "warning", VC.INVALID_DATE, 
                "Date Counseled", f"Counseling date {formatted_date} is before 2023-10-01"
            )
    
    # Validate session type and contact hours
    session_type = row.get('Type of Session', 'Telephone')
    contact_hours = row.get('Duration (hours)', '0')
    
    if session_type not in ['Prepare Only', 'Training', 'Update Only'] and float(contact_hours or 0) <= 0:
        validator.add_issue(
            record_id, "warning", VC.INVALID_VALUE, 
            "Contact Hours", f"Contact Hours should be greater than 0 for {session_type} sessions"
        )
    
    # Validate counselor notes length
    counselor_notes = row.get('Comments', '')
    if len(counselor_notes) > 1000:
        validator.add_issue(
            record_id, "info", VC.TRUNCATED_VALUE, 
            "Counselor Notes", f"Counselor notes truncated from {len(counselor_notes)} to 1000 characters"
        )
    
    return record_valid

def analyze_country_data(csv_rows):
    """
    Analyzes all country values in the dataset to identify problematic values.
    
    Args:
        csv_rows: List of dictionaries from CSV reader
        
    Returns:
        Dictionary with analysis of country values
    """
    country_values = {}
    for row in csv_rows:
        country = row.get('Mailing Country', '')
        if country:
            country_str = str(country).strip()
            if country_str in country_values:
                country_values[country_str] += 1
            else:
                country_values[country_str] = 1
    return country_values

def analyze_csv_data(csv_rows):
    """
    Analyzes the CSV data for potential issues before conversion.
    
    Args:
        csv_rows: List of dictionaries from CSV reader
        
    Returns:
        Dictionary with analysis results
    """
    analysis = {
        'row_count': len(csv_rows),
        'missing_contact_id': 0,
        'missing_names': 0,
        'invalid_dates': 0,
        'country_values': analyze_country_data(csv_rows)
    }
    
    # Count various data issues
    for row in csv_rows:
        if not row.get('Contact ID'):
            analysis['missing_contact_id'] += 1
        
        if not row.get('Last Name') or not row.get('First Name'):
            analysis['missing_names'] += 1
        
        date_fields = ['Date', 'Client Signature - Date', 'Business Start Date']
        for field in date_fields:
            if row.get(field) and not format_date(row.get(field)):
                analysis['invalid_dates'] += 1
                break
    
    return analysis  
