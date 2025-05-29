#!/usr/bin/env python3
"""
CSV to XML Converter for SBA Training Reports

This script processes a CSV file containing training participant data
and generates an XML document that conforms to the SBA_NEXUS_Training.xsd schema.
"""

import pandas as pd
import xml.dom.minidom as md
from xml.etree.ElementTree import Element, SubElement, tostring
import re
from datetime import datetime
import argparse
import os
import logging

import logging # Keep standard logging import for levels like logging.INFO
# Local logger configuration will be replaced by ConversionLogger
# logger = logging.getLogger(__name__) # To be replaced

from xml_utils import create_element, escape_xml
from logging_util import ConversionLogger # Import ConversionLogger
from data_cleaning import format_date as clean_format_date # Renamed to avoid confusion
from data_cleaning import standardize_state_name, map_value
import config # Import the entire config module

def convert_csv_to_xml(csv_file_path, output_xml_path):
    """
    Convert CSV data to XML format according to SBA training report schema
    
    Args:
        csv_file_path (str): Path to the input CSV file
        output_xml_path (str): Path to save the output XML file
    """
    try:
        # Read CSV file
        logger.info(f"Reading CSV file: {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        logger.info(f"CSV loaded successfully with {len(df)} records")
        
        # Print column names to help with debugging
        logger.info(f"CSV columns: {', '.join(df.columns)}")
        
        # Group by training event
        event_groups = df.groupby('Class/Event ID')
        logger.info(f"Found {len(event_groups)} unique training events")
        
        # Create root element
        root = Element('ManagementTrainingReport')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        
        # Process each training group
        for event_id, group_df in event_groups:
            if len(group_df) == 0:
                continue
                
            # Get first record for event details
            first_record = group_df.iloc[0]
            
            # Create training record element
            record = create_element(root, 'ManagementTrainingRecord')
            
            # Partner Training Number - Use Class/Event ID directly (will never be missing)
            event_id_text = str(first_record.get('Class/Event ID', ''))
            create_element(record, 'PartnerTrainingNumber', event_id_text)
            logger.info(f"Using Class/Event ID as PartnerTrainingNumber: {event_id_text}")
            
            # Location - using the specified fixed value of 249003
            location = create_element(record, 'Location')
            create_element(location, 'LocationCode', config.DEFAULT_LOCATION_CODE)  # Use from config
            
            # Funding Source - always omit as requested
            fs_value = map_funding_source(first_record.get('Funding Source', ''))
            if fs_value:  # This will always be false now, but keeping the structure for future flexibility
                create_element(record, 'FundingSource', fs_value)
            
            # Date Training Started - from CSV if available
            date_val = first_record.get('Start Date', '')
            # Define formats for this specific call
            date_formats_for_class_converter = ['%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y', '%m/%d/%y']
            # Using a generic default like an empty string or a far past date might be better if the XSD allows optional.
            # For now, sticking to the original '2023-12-12' default for this specific converter.
            formatted_date = clean_format_date(date_val, input_formats=date_formats_for_class_converter, default_return='2023-12-12') 
            create_element(record, 'DateTrainingStarted', formatted_date)
            
            # Number of Sessions - using specified default
            create_element(record, 'NumberOfSessions', config.DEFAULT_TRAINING_SESSIONS)
            
            # Total Training Hours - using specified default
            create_element(record, 'TotalTrainingHours', config.DEFAULT_TRAINING_HOURS)
            
            # Training Title - from CSV
            title_val = first_record.get('Class/Event Name', '')
            if not title_val:
                title_val = f"{config.DEFAULT_TRAINING_EVENT_TITLE_PREFIX}{event_id_text}" # Use prefix from config
            create_element(record, 'TrainingTitle', escape_xml(title_val))
            
            # Training Location - from CSV or use default location
            location_data = get_location_data(first_record) # This function now uses config defaults
            training_location = create_element(record, 'TrainingLocation')
            
            if location_data['city']: # city comes from get_location_data, which uses config defaults
                create_element(training_location, 'City', location_data['city'])
                
            if location_data['state']: # state comes from get_location_data, which uses config defaults
                create_element(training_location, 'State', location_data['state'])
                
            if location_data['zip_code']: # zip_code comes from get_location_data, which uses config defaults
                create_element(training_location, 'ZipCode', location_data['zip_code'])
                
            country_element = create_element(training_location, 'Country')
            create_element(country_element, 'Code', location_data['country']) # country from get_location_data
            
            # Calculate demographics from CSV data
            demographics = calculate_demographics(group_df)
            
            # Number Trained section - Total is always required
            number_trained = create_element(record, 'NumberTrained')
            
            create_element(number_trained, 'Total', str(demographics['total']))
            
            # Only include demographic fields if values are present
            if demographics['currently_in_business'] > 0:
                create_element(number_trained, 'CurrentlyInBusiness', str(demographics['currently_in_business']))
            
            if demographics['not_in_business'] > 0:
                create_element(number_trained, 'NotYetInBusiness', str(demographics['not_in_business']))
            
            if demographics['disabilities'] > 0:
                create_element(number_trained, 'PersonWithDisabilities', str(demographics['disabilities']))
            
            if demographics['female'] > 0:
                create_element(number_trained, 'Female', str(demographics['female']))
            
            if demographics['male'] > 0:
                create_element(number_trained, 'Male', str(demographics['male']))
            
            if demographics['active_duty'] > 0:
                create_element(number_trained, 'ActiveDuty', str(demographics['active_duty']))
            
            if demographics['veterans'] > 0:
                create_element(number_trained, 'Veterans', str(demographics['veterans']))
            
            if demographics['service_disabled_veterans'] > 0:
                create_element(number_trained, 'ServiceDisabledVeterans', str(demographics['service_disabled_veterans']))
            
            if demographics['reserve_guard'] > 0:
                create_element(number_trained, 'MemberOfReserveOrNationalGuard', str(demographics['reserve_guard']))
            
            if demographics['military_spouse'] > 0:
                create_element(number_trained, 'SpouseOfMilitaryMember', str(demographics['military_spouse']))
            
            # Race - only include if there's at least one race with data
            if any(value > 0 for value in demographics['race'].values()):
                race_element = create_element(number_trained, 'Race')
                
                # Only include specific race elements if they have values
                if demographics['race']['asian'] > 0:
                    create_element(race_element, 'Asian', str(demographics['race']['asian']))
                
                if demographics['race']['black'] > 0:
                    create_element(race_element, 'BlackOrAfricanAmerican', str(demographics['race']['black']))
                
                if demographics['race']['native_american'] > 0:
                    create_element(race_element, 'NativeAmericanOrAlaskaNative', str(demographics['race']['native_american']))
                
                if demographics['race']['pacific_islander'] > 0:
                    create_element(race_element, 'NativeHawaiianOrPacificIslander', str(demographics['race']['pacific_islander']))
                
                if demographics['race']['white'] > 0:
                    create_element(race_element, 'White', str(demographics['race']['white']))
                
                if demographics['race']['middle_eastern'] > 0:
                    create_element(race_element, 'MiddleEastern', str(demographics['race']['middle_eastern']))
                
                if demographics['race']['north_african'] > 0:
                    create_element(race_element, 'NorthAfrican', str(demographics['race']['north_african']))
            
            # Ethnicity - only include if there's ethnicity data
            if any(value > 0 for value in demographics['ethnicity'].values()):
                ethnicity_element = create_element(number_trained, 'Ethnicity')
                
                if demographics['ethnicity']['hispanic'] > 0:
                    create_element(ethnicity_element, 'HispanicOrLatinoOrigin', str(demographics['ethnicity']['hispanic']))
                
                if demographics['ethnicity']['non_hispanic'] > 0:
                    create_element(ethnicity_element, 'NonHispanicOrLatinoOrigin', str(demographics['ethnicity']['non_hispanic']))
            
            # Number Minorities Trained - only include if there are minorities
            if demographics['minorities'] > 0:
                minorities_element = create_element(record, 'NumberUnderservedTrained')
                create_element(minorities_element, 'Total', str(demographics['minorities']))
            
            # Training Topic - from CSV
            training_topic_element = create_element(record, 'TrainingTopic')
            topic_val = first_record.get('Training Topic', '')
            # Use mappings and default from config
            mapped_topic = map_value(topic_val, config.TRAINING_TOPIC_MAPPINGS, default_value=config.DEFAULT_TRAINING_TOPIC, case_sensitive=False)
            # Note: The original classDataConverter.map_training_topic had more complex logic
            # for partial matches against VALID_TRAINING_TOPICS. map_value with TRAINING_TOPIC_MAPPINGS
            # primarily handles direct key matches (case-insensitive). If a key isn't in
            # TRAINING_TOPIC_MAPPINGS, it gets DEFAULT_TRAINING_TOPIC.
            # This simplification aligns with using the generic map_value.
            # If the more complex logic (like keyword search in VALID_TRAINING_TOPICS) is strictly needed,
            # map_value might need to be enhanced, or a more specific mapping function retained/re-introduced.
            create_element(training_topic_element, 'Code', mapped_topic)
            
            # Training Partners - always Women's Business Center
            partners_element = create_element(record, 'TrainingPartners')
            
            # Add Women's Business Center as partner
            create_element(partners_element, 'Code', config.DEFAULT_TRAINING_PARTNER_CODE)
            
            # Program Format Type - directly from 'Class/Event Type' column
            format_val = first_record.get('Class/Event Type', '')
            # Use mappings and default from config
            program_format_text = map_value(format_val, config.PROGRAM_FORMAT_MAPPINGS, default_value=config.DEFAULT_PROGRAM_FORMAT, case_sensitive=False)
            create_element(record, 'ProgramFormatType', program_format_text)
            logger.info(f"Using Program Format Type: {program_format_text} from value: {format_val}")
            
            # Dollar Amount of Fees - always 0 or omit
            create_element(record, 'DollarAmountOfFees', config.DEFAULT_TRAINING_FEES)
            
            # Language - include English by default
            language_element = create_element(record, 'Language')
            
            # Add default English language
            create_element(language_element, 'Code', config.DEFAULT_LANGUAGE) # Use from config
            
            # Sponsor Name and Cosponsor Name - leave blank
            # SponsorName is completely omitted as requested
            
            # Only include CosponsorName if explicitly found in CSV
            cosponsor_name = extract_cosponsor_name(first_record)
            if cosponsor_name and cosponsor_name.strip() and cosponsor_name.lower() != 'n/a':
                create_element(record, 'CosponsorsName', cosponsor_name)
        
        # Convert to formatted XML string
        rough_string = tostring(root, 'utf-8')
        reparsed = md.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")
        
        # Remove empty lines to clean up output
        pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
        
        # Write to output file
        with open(output_xml_path, 'w') as f:
            f.write(pretty_xml)
            
        logger.info(f"XML file successfully created at {output_xml_path}")
        
    except Exception as e:
        logger.error(f"Error converting CSV to XML: {str(e)}", exc_info=True)
        raise

# Removed local format_date, will use data_cleaning.format_date

def get_location_data(record):
    """Extract location information from a record"""
    city = None
    state = None
    zip_code = None
    location_found = False
    
    # Try to get city
    for field in ['City', 'city', 'Address', 'Street Line 1']:
        if field in record and not pd.isna(record[field]):
            city_val = str(record[field])
            # Try to extract city from address
            if field in ['Address', 'Street Line 1'] and ',' in city_val:
                parts = city_val.split(',')
                if len(parts) > 1:
                    city = escape_xml(parts[1].strip()) # Apply escaping
                    location_found = True
                    break
            else:
                city = escape_xml(city_val) # Apply escaping
                location_found = True
                break
    
    # Try to get state
    for field in ['State/Province', 'State', 'state']:
        if field in record and not pd.isna(record[field]):
            state = escape_xml(str(record[field])) # Apply escaping
            if state:
                location_found = True
            break
    
    # Try to get zip code
    for field in ['Zip/Postal Code', 'Zip', 'zip', 'ZipCode', 'Zip code']:
        if field in record and not pd.isna(record[field]):
            zip_val = str(record[field])
            # Extract first 5 digits
            zip_match = re.search(r'\d{5}', zip_val)
            if zip_match:
                zip_code = escape_xml(zip_match.group(0)) # Apply escaping
                location_found = True
                break
    
    # If we couldn't determine a clear location, use the specified default
    if not location_found or not (city and state and zip_code):
        # Use specified defaults from config
        city = config.DEFAULT_TRAINING_LOCATION_CITY
        state = config.DEFAULT_TRAINING_LOCATION_STATE
        zip_code = config.DEFAULT_TRAINING_LOCATION_ZIP
        logger.info(f"Using default location: {city}, {state} {zip_code}")
    
    # Standardize the state name using the new function.
    # If state was defaulted above, it will be standardized (e.g. "Iowa" -> "Iowa").
    # If state came from CSV, it will be standardized.
    # If standardization fails (e.g. invalid state from CSV and no default triggered above),
    # it defaults to config.DEFAULT_TRAINING_LOCATION_STATE.
    state = standardize_state_name(state, default_return=config.DEFAULT_TRAINING_LOCATION_STATE)
    
    return {
        'city': city, 
        'state': state, 
        'zip_code': zip_code, 
        'country': config.DEFAULT_TRAINING_LOCATION_COUNTRY # Use from config
    }

def calculate_demographics(df):
    """Calculate demographic information from a group of records"""
    total = len(df)
    
    # Business status
    currently_in_business = 0
    not_in_business = 0
    
    # Try to find business status column
    business_col = None
    for col in ['Currently in Business?', 'Currently in Business', 'In Business']:
        if col in df.columns:
            business_col = col
            break
    
    if business_col:
        currently_in_business = sum(df[business_col].fillna('').astype(str).str.lower().str.contains('yes|true|1|y'))
        not_in_business = total - currently_in_business
    
    # Gender counts
    female = 0
    male = 0
    
    # Find gender column
    gender_col = None
    for col in ['Gender', 'gender', 'Sex']:
        if col in df.columns:
            gender_col = col
            break
    
    if gender_col:
        female = sum(df[gender_col].fillna('').astype(str).str.lower().str.contains('female|f|woman|women'))
        male = sum(df[gender_col].fillna('').astype(str).str.lower().str.contains('male|m|man|men'))
    
    # Disabilities
    disabilities = 0
    
    # Find disabilities column
    disability_col = None
    for col in ['Disabilities', 'Disability', 'Has Disability']:
        if col in df.columns:
            disability_col = col
            break
    
    if disability_col:
        disabilities = sum(df[disability_col].fillna('').astype(str).str.lower().str.contains('yes|true|1|y'))
    
    # Military status
    active_duty = 0
    veterans = 0
    service_disabled_veterans = 0
    reserve_guard = 0
    military_spouse = 0
    
    # Find military status column
    military_col = None
    for col in ['Military Status', 'Military', 'Veteran Status']:
        if col in df.columns:
            military_col = col
            break
    
    if military_col:
        military_status = df[military_col].fillna('')
        active_duty = sum(military_status.astype(str).str.lower().str.contains('active duty|active-duty'))
        veterans = sum(military_status.astype(str).str.lower().str.contains('veteran'))
        service_disabled_veterans = sum(military_status.astype(str).str.lower().str.contains('service disabled|disabled vet'))
        reserve_guard = sum(military_status.astype(str).str.lower().str.contains('reserve|guard'))
        military_spouse = sum(military_status.astype(str).str.lower().str.contains('spouse'))
    
    # Race counts
    race = {
        'asian': 0,
        'black': 0,
        'native_american': 0,
        'pacific_islander': 0,
        'white': 0,
        'middle_eastern': 0,
        'north_african': 0
    }
    
    # Find race column
    race_col = None
    for col in ['Race', 'race', 'Racial Background']:
        if col in df.columns:
            race_col = col
            break
    
    if race_col:
        race_data = df[race_col].fillna('')
        race['asian'] = sum(race_data.astype(str).str.lower().str.contains('asian'))
        race['black'] = sum(race_data.astype(str).str.lower().str.contains('black|african american'))
        race['native_american'] = sum(race_data.astype(str).str.lower().str.contains('american indian|alaska native|native american'))
        race['pacific_islander'] = sum(race_data.astype(str).str.lower().str.contains('hawaiian|pacific islander'))
        race['white'] = sum(race_data.astype(str).str.lower().str.contains('white|caucasian'))
        race['middle_eastern'] = sum(race_data.astype(str).str.lower().str.contains('middle east'))
        race['north_african'] = sum(race_data.astype(str).str.lower().str.contains('north africa'))
    
    # Ethnicity counts
    ethnicity = {
        'hispanic': 0,
        'non_hispanic': 0
    }
    
    # Find ethnicity column
    ethnicity_col = None
    for col in ['Ethnicity', 'ethnicity', 'Ethnic Background']:
        if col in df.columns:
            ethnicity_col = col
            break
    
    if ethnicity_col:
        ethnicity_data = df[ethnicity_col].fillna('')
        ethnicity['hispanic'] = sum(ethnicity_data.astype(str).str.lower().str.contains('hispanic|latino'))
        # Count non-empty values that don't contain Hispanic/Latino
        non_hispanic_mask = (~ethnicity_data.astype(str).str.lower().str.contains('hispanic|latino')) & (ethnicity_data != '')
        ethnicity['non_hispanic'] = sum(non_hispanic_mask)
    
    # Calculate minorities (sum of non-white races and Hispanic ethnicity)
    minorities = (race['asian'] + race['black'] + race['native_american'] + 
                 race['pacific_islander'] + race['middle_eastern'] + 
                 race['north_african'] + ethnicity['hispanic'])
    
    # Ensure total is at least 2 (XSD minimum)
    total = max(total, 2)
    
    # Return actual values without defaults
    return {
        'total': total,
        'currently_in_business': currently_in_business,
        'not_in_business': not_in_business,
        'disabilities': disabilities,
        'female': female,
        'male': male,
        'active_duty': active_duty,
        'veterans': veterans,
        'service_disabled_veterans': service_disabled_veterans,
        'reserve_guard': reserve_guard,
        'military_spouse': military_spouse,
        'race': race,
        'ethnicity': ethnicity,
        'minorities': minorities
    }

# map_funding_source was removed and its logic inlined.
# map_training_topic was removed and replaced by map_value.
# map_program_format was removed and replaced by map_value.
# map_state was removed and its logic merged into data_cleaning.standardize_state_name.

def extract_cosponsor_name(record):
    """Extract cosponsor name from a record"""
    # Default cosponsor
    cosponsor = ''
    
    # Try to find cosponsor information in the record
    for field in ['Cosponsor', 'CosponsorsName', 'Partner Organization']:
        if field in record and not pd.isna(record[field]):
            cosponsor_val = str(record[field])
            if cosponsor_val:
                cosponsor = escape_xml(cosponsor_val) # Apply escaping
                break
    
    return cosponsor

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert CSV file to SBA XML format')
    parser.add_argument('input_csv', help='Path to the input CSV file')
    parser.add_argument('output_xml', help='Path for the output XML file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--log-file', help='Optional path to save log output to a file.')

    args = parser.parse_args()
    
    # Setup logger using ConversionLogger
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = ConversionLogger(
        logger_name="ClassDataConverter",
        log_level=log_level,
        log_to_file=bool(args.log_file), # True if a path is provided
        log_file_path=args.log_file if args.log_file else None
    ).logger # Get the actual logger instance
    
    # Check if input file exists
    if not os.path.isfile(args.input_csv):
        logger.error(f"Input file not found: {args.input_csv}")
        exit(1)
    
    # Convert CSV to XML
    try:
        convert_csv_to_xml(args.input_csv, args.output_xml)
        print(f"Successfully converted {args.input_csv} to {args.output_xml}")
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        exit(1)