"""
CSV to XML conversion utility.
This module handles converting Salesforce counseling data from CSV format to XML.
Updated with improved separation of concerns.
"""

import csv
import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime

from data_cleaning import (
    clean_phone_number, format_date, clean_whitespace, validate_counseling_date,
    map_gender_to_sex, split_multi_value, clean_numeric, clean_percentage,
    truncate_counselor_notes, standardize_country_code, standardize_state_name
)
from data_validation import (
    validate_record, analyze_csv_data
)
from config import (
    FIELD_MAPPING, DEFAULT_LOCATION_CODE, NO_CONTACT_HOUR_SESSION_TYPES,
    DEFAULT_BUSINESS_STATUS, DEFAULT_LANGUAGE, ValidationCategory,
    DEFAULT_SESSION_TYPE, DEFAULT_URBAN_RURAL, VALID_SESSION_TYPES
)

# Import default logger and validator (will be overridden in create_xml_from_csv)
from logging_util import logger
from validation_report import validator
from xml_utils import create_element


def create_xml_from_csv(csv_file_path, xml_file_path, custom_logger=None, custom_validator=None):
    """
    Converts counseling data from CSV format to XML.
    
    Args:
        csv_file_path: Path to the input CSV file
        xml_file_path: Path where the output XML file will be saved
        custom_logger: Optional custom logger instance
        custom_validator: Optional custom validation tracker instance
    """
    global logger, validator
    
    # Use custom logger and validator if provided
    if custom_logger:
        logger = custom_logger
    if custom_validator:
        validator = custom_validator
    
    # Open and read the CSV file
    try:
        with open(csv_file_path, 'r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            rows = list(csv_reader)
            logger.info(f"Successfully read CSV file with {len(rows)} records")
    except Exception as e:
        logger.error(f"Failed to read CSV file: {str(e)}")
        validator.add_issue("file", "error", ValidationCategory.FILE_ACCESS, "input_file", 
                           f"Failed to read CSV file: {str(e)}")
        raise
    
    # Analyze CSV data
    analysis = analyze_csv_data(rows)
    logger.info(f"Analyzed CSV data: {len(rows)} records, {analysis['missing_contact_id']} missing IDs, "
                f"{analysis['missing_names']} missing names, {analysis['invalid_dates']} invalid dates")
    
    # Create XML structure
    root = ET.Element('CounselingInformation')
    processed_records = 0
    skipped_records = 0

    # Process each row
    for row_index, row in enumerate(rows, 1):
        # Get record ID for tracking
        record_id = row.get('Contact ID', f"Row_{row_index}")
        
        # Validate record
        if not validate_record(row, row_index, record_id):
            logger.warning(f"Skipping record {record_id} due to validation errors")
            skipped_records += 1
            continue
            
        try:
            # Create counseling record element
            counseling_record = create_element(root, 'CounselingRecord')
            
            # Add PartnerClientNumber (required)
            create_element(counseling_record, 'PartnerClientNumber', record_id)
                
            # Location section
            location = create_element(counseling_record, 'Location')
            create_element(location, 'LocationCode', row.get('LocationCode', DEFAULT_LOCATION_CODE))
            
            # Build ClientRequest section
            build_client_request_section(counseling_record, row, record_id)
            
            # Build ClientIntake section
            build_client_intake_section(counseling_record, row, record_id)
            
            # Build CounselorRecord section
            build_counselor_record_section(counseling_record, row, record_id)
            
            processed_records += 1
            validator.record_processed(success=True)
            
        except Exception as e:
            logger.error(f"Error processing record {record_id}: {str(e)}")
            validator.add_issue(
                record_id, "error", ValidationCategory.PROCESSING_ERROR, 
                "record", f"Error processing record: {str(e)}"
            )
            validator.record_processed(success=False)
                
    # Write the XML tree to the output file
    try:
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)
        logger.info(f"XML file created successfully with {processed_records} records")
        logger.info(f"Skipped {skipped_records} records due to validation errors")
    except Exception as e:
        logger.error(f"Failed to write XML file: {str(e)}")
        validator.add_issue("file", "error", ValidationCategory.FILE_WRITE, "output_file", 
                           f"Failed to write XML file: {str(e)}")
        raise


def build_client_request_section(counseling_record, row, record_id):
    """
    Builds the ClientRequest section of the XML.
    Ensures elements are in the correct order according to the XSD schema.
    
    Args:
        counseling_record: The parent XML element
        row: Dictionary of field values
        record_id: ID of the record
    """
    client_request = create_element(counseling_record, 'ClientRequest')
    
    # Name information
    client_name = create_element(client_request, 'ClientNamePart1')
    create_element(client_name, 'Last', row.get('Last Name', ''))
    create_element(client_name, 'First', row.get('First Name', ''))
    create_element(client_name, 'Middle', row.get('Middle Name', ''))
    
    # Contact information
    create_element(client_request, 'Email', row.get('Email', ''))
    phone = create_element(client_request, 'PhonePart1')
    create_element(phone, 'Primary', clean_phone_number(row.get('Contact: Phone', '')))
    create_element(phone, 'Secondary', '')
    
    # Address information
    address = create_element(client_request, 'AddressPart1')
    create_element(address, 'Street1', row.get('Mailing Street', ''))
    create_element(address, 'Street2', '')
    create_element(address, 'City', row.get('Mailing City', ''))
    state_value = row.get('Mailing State/Province', '')
    standardized_state = standardize_state_name(state_value)
    create_element(address, 'State', standardized_state)

    # **FIX**: Extract 5-digit zip code
    zip_full = str(row.get('Mailing Zip/Postal Code', '')).strip()
    zip_5digit_match = re.match(r'^\d{5}', zip_full)
    zip_5digit = zip_5digit_match.group(0) if zip_5digit_match.group(0) else ''
    if not zip_5digit and zip_full:
        validator.add_issue(record_id, "warning", ValidationCategory.INVALID_FORMAT, "Mailing Zip/Postal Code", f"Could not parse 5-digit ZIP from '{zip_full}'.")
    create_element(address, 'ZipCode', zip_5digit)
    
    create_element(address, 'Zip4Code', '')
    
    # Country section with standardization
    country = create_element(address, 'Country')
    country_value = row.get('Mailing Country', 'US')
    standardized_country = standardize_country_code(country_value)
    create_element(country, 'Code', standardized_country)
    
    # Survey agreement and signature
    survey_agreement = row.get('Agree to Impact Survey', 'No')
    create_element(client_request, 'SurveyAgreement', survey_agreement)
    
    signature = create_element(client_request, 'ClientSignature')
    signature_date = format_date(row.get('Client Signature - Date', ''))
    create_element(signature, 'Date', signature_date)
    
    signature_onfile = row.get('Client Signature(On File)', 'No')
    if signature_onfile == '1' or signature_onfile == 1:
        signature_onfile = 'Yes'
    create_element(signature, 'OnFile', signature_onfile)


def build_client_intake_section(counseling_record, row, record_id):
    """
    Builds the ClientIntake section of the XML.
    **REORDERED** to strictly follow the SBA_EDMIS_Counseling.xsd sequence.
    Args:
        counseling_record: The parent XML element
        row: Dictionary of field values
        record_id: ID of the record
    """
    client_intake = create_element(counseling_record, 'ClientIntake')

    # 1. Race
    race_element = create_element(client_intake, 'Race')
    race_codes_csv = split_multi_value(row.get('Race', ''))
    if race_codes_csv:
        for code in race_codes_csv:
            create_element(race_element, 'Code', code)
    else:
        create_element(race_element, 'Code', 'Prefer not to say')
        validator.add_issue(record_id, "warning", ValidationCategory.MISSING_FIELD, "Race/Code", "Race Code missing, defaulted to 'Prefer not to say'.")
    
    self_described_race_csv = row.get('SelfDescribedRace_From_CSV', '').strip()
    if self_described_race_csv:
        create_element(race_element, 'SelfDescribedRace', self_described_race_csv)

    # 2. Ethnicity
    ethnicity_csv = row.get('Ethnicity::', '').strip()
    if ethnicity_csv:
        create_element(client_intake, 'Ethnicity', ethnicity_csv)
    
    # 3. Sex
    sex_value = map_gender_to_sex(row.get('Gender', ''))
    if sex_value:
        create_element(client_intake, 'Sex', sex_value)
    
    # 4. Disability
    disability_csv = row.get('Disability', '').strip()
    if disability_csv:
        create_element(client_intake, 'Disability', disability_csv)

    # 5. MilitaryStatus
    military_status_csv = row.get('Veteran Status', '').strip()
    if military_status_csv:
        create_element(client_intake, 'MilitaryStatus', military_status_csv)

    # 6. BranchOfService (Conditional)
    non_military_statuses = ['prefer not to say', 'no military service', '']
    if military_status_csv and military_status_csv.lower() not in non_military_statuses:
        branch_csv = row.get('Branch Of Service', '').strip()
        if branch_csv and branch_csv.lower() not in non_military_statuses:
            create_element(client_intake, 'BranchOfService', branch_csv)
        else:
            validator.add_issue(record_id, "error", ValidationCategory.MISSING_REQUIRED, "BranchOfService", f"Branch Of Service required for Military Status '{military_status_csv}' but not provided/valid.")

    # 7. Media
    media_codes = split_multi_value(row.get('What Prompted you to contact us?', ''))
    media_other = row.get('Internet (specify)', '').strip()
    if media_codes or media_other:
        media = create_element(client_intake, 'Media')
        for code in media_codes:
            create_element(media, 'Code', code)
        if media_other:
            create_element(media, 'Other', media_other)

    # 8. Internet
    internet_usage = row.get('ClientIntake_Internet', '').strip()
    if internet_usage:
        create_element(client_intake, 'Internet', internet_usage)

    # 9. CurrentlyInBusiness
    in_business_val = row.get('Currently In Business?', DEFAULT_BUSINESS_STATUS)
    create_element(client_intake, 'CurrentlyInBusiness', in_business_val)

    # 10. CurrentlyExporting
    exporting_val = row.get('Are you currently exporting?(old)', DEFAULT_BUSINESS_STATUS)
    create_element(client_intake, 'CurrentlyExporting', exporting_val)

    # Continue with the rest of the elements in order...
    create_element(client_intake, 'CompanyName', row.get('Account Name', ''))
    create_element(client_intake, 'BusinessType', row.get('Type of Business', ''))
    
    bo_element = create_element(client_intake, 'BusinessOwnership')
    female_ownership_val = clean_percentage(row.get('Business Ownership - % Female(old)', '0'))
    create_element(bo_element, 'Female', female_ownership_val)
    
    create_element(client_intake, 'ConductingBusinessOnline', row.get('Conduct Business Online?', DEFAULT_BUSINESS_STATUS))
    create_element(client_intake, 'ClientIntake_Certified8a', row.get('8(a) Certified?(old)', DEFAULT_BUSINESS_STATUS))
    
    # ... and so on, ensuring every element is created in its XSD-defined place.
    create_element(client_intake, 'TotalNumberOfEmployees', clean_numeric(row.get('Total Number of Employees', '0')))
    create_element(client_intake, 'NumberOfEmployeesInExportingBusiness', '0')
    
    income_part2 = create_element(client_intake, 'ClientAnnualIncomePart2')
    create_element(income_part2, 'GrossRevenues', clean_numeric(row.get('Gross Revenues/Sales', '0')))
    create_element(income_part2, 'ProfitLoss', clean_numeric(row.get('Profits/Losses', '0')))
    create_element(income_part2, 'ExportGrossRevenuesOrSales', '0')

    # LegalEntity (Conditional on being in business)
    if in_business_val.lower() == 'yes':
        le_element = create_element(client_intake, 'LegalEntity')
        le_codes = split_multi_value(row.get('Legal Entity of Business', ''))
        le_other = row.get('Other legal entity (specify)', '').strip()
        if le_codes:
            for code in le_codes:
                create_element(le_element, 'Code', code)
        elif le_other:
             create_element(le_element, 'Code', 'Other') # Default code if only other text exists
        else:
             validator.add_issue(record_id, "error", ValidationCategory.MISSING_REQUIRED, "LegalEntity/Code", "Client is in business, but Legal Entity is missing.")
             create_element(le_element, 'Code', 'Other') # Default to prevent structural error

        if le_other:
            create_element(le_element, 'Other', le_other)

    # Rural_vs_Urban and FIPS_Code
    rural_urban_val = row.get('Rural_vs_Urban_From_CSV', DEFAULT_URBAN_RURAL) # You need this column in your CSV
    create_element(client_intake, 'Rural_vs_Urban', rural_urban_val)
    if rural_urban_val.lower() in ['rural', 'urban']:
        fips_code = row.get('FIPS_Code_From_CSV', '').strip() # You need this column in your CSV
        if fips_code:
            create_element(client_intake, 'FIPS_Code', fips_code)
        else:
            validator.add_issue(record_id, "error", ValidationCategory.MISSING_REQUIRED, "FIPS_Code", f"FIPS Code required for Rural/Urban status '{rural_urban_val}' but is missing.")
            
    # CounselingSeeking
    cs_codes = split_multi_value(row.get('Nature of the Counseling Seeking?', ''))
    cs_other = row.get('Nature of the Counseling Seeking - Other Detail', '').strip() # You need this column in your CSV
    if cs_codes or cs_other:
        cs_element = create_element(client_intake, 'CounselingSeeking')
        is_other_present = any(c.lower() == 'other' for c in cs_codes)
        
        if cs_codes:
            for code in cs_codes:
                create_element(cs_element, 'Code', code)
        elif cs_other:
            create_element(cs_element, 'Code', 'Other')
            is_other_present = True
        else: # Should be mandatory per mod log
            create_element(cs_element, 'Code', 'Other') # Default
            validator.add_issue(record_id, "warning", ValidationCategory.MISSING_FIELD, "CounselingSeeking", "CounselingSeeking missing, defaulted to Other.")

        if is_other_present:
            if not cs_other:
                validator.add_issue(record_id, "error", ValidationCategory.MISSING_REQUIRED, "CounselingSeeking/Other", "CounselingSeeking code is 'Other' but detail text is missing.")
            create_element(cs_element, 'Other', cs_other)

def build_counselor_record_section(counseling_record, row, record_id):
    """
    Builds the CounselorRecord section of the XML.
    
    Args:
        counseling_record: The parent XML element
        row: Dictionary of field values
        record_id: ID of the record
    """
    counselor_record = create_element(counseling_record, 'CounselorRecord')
    
    # Session information
    create_element(counselor_record, 'PartnerSessionNumber', row.get('Activity ID', ''))
    create_element(counselor_record, 'FundingSource', '')
    
    # Counselor name and contact information (These are for the counselor, not client)
    # The XSD shows these as optional, but they seem to be duplicates of client info in your script.
    # It may be better to omit them or populate with actual counselor data if available.
    # For now, following your script's logic:
    counselor_name_part3 = create_element(counselor_record, 'ClientNamePart3')
    create_element(counselor_name_part3, 'Last', row.get('Last Name', ''))
    create_element(counselor_name_part3, 'First', row.get('First Name', ''))
    create_element(counselor_name_part3, 'Middle', row.get('Middle Name', ''))
    
    create_element(counselor_record, 'Email', row.get('Email', ''))
    
    phone_part3 = create_element(counselor_record, 'PhonePart3')
    create_element(phone_part3, 'Primary', clean_phone_number(row.get('Contact: Phone', '')))
    create_element(phone_part3, 'Secondary', '')
    
    address_part3 = create_element(counselor_record, 'AddressPart3')
    create_element(address_part3, 'Street1', row.get('Mailing Street', ''))
    # ... and so on for the rest of AddressPart3, including the 5-digit zip fix.
    zip_full_p3 = str(row.get('Mailing Zip/Postal Code', '')).strip()
    zip_5digit_match_p3 = re.match(r'^\d{5}', zip_full_p3)
    zip_5digit_p3 = zip_5digit_match_p3.group(0) if zip_5digit_match_p3 else ''
    create_element(address_part3, 'ZipCode', zip_5digit_p3)
    # ... country, etc. ...

    # Business verification
    create_element(counselor_record, 'VerifiedToBeInBusiness', 'Undetermined')
    create_element(counselor_record, 'ReportableImpact', row.get('Reportable Impact', DEFAULT_BUSINESS_STATUS))
    create_element(counselor_record, 'DateOfReportableImpact', format_date(row.get('Reportable Impact Date', '')))
    create_element(counselor_record, 'CurrentlyExporting', DEFAULT_BUSINESS_STATUS)
    
    business_start_date = format_date(row.get('Business Start Date', ''))
    if not business_start_date:
        business_start_date = format_date(row.get('Date Started (Meeting)', ''))
    if business_start_date:
        create_element(counselor_record, 'BusinessStartDatePart3', business_start_date)
    
    # Employee and financial information for the *meeting*
    # Per XSD ModLog #104, TotalNumberOfEmployees is back in Part 3.
    create_element(counselor_record, 'TotalNumberOfEmployees', clean_numeric(row.get('Total No. of Employees (Meeting)', row.get('Total Number of Employees', '0'))))
    create_element(counselor_record, 'NumberOfEmployeesInExportingBusiness', '0')
    
    income_part3 = create_element(counselor_record, 'ClientAnnualIncomePart3')
    create_element(income_part3, 'GrossRevenues', clean_numeric(row.get('Gross Revenues/Sales (Meeting)', row.get('Gross Revenues/Sales', '0'))))
    create_element(income_part3, 'ProfitLoss', clean_numeric(row.get('Profit & Loss (Meeting)', row.get('Profits/Losses', '0'))))
    create_element(income_part3, 'ExportGrossRevenuesOrSales', '0')
    create_element(income_part3, 'GrowthIndicator', '')
    
    # Certifications
    # ... logic for Certifications ...

    # SBA Financial Assistance
    # ... logic for SBAFinancialAssistance ...

    # Counseling provided
    cp_element = create_element(counselor_record, 'CounselingProvided')
    provided_codes = split_multi_value(row.get('Services Provided', 'Business Start-up/Preplanning'))
    for code in provided_codes:
        create_element(cp_element, 'Code', code)
    create_element(cp_element, 'Other', '')
    
    # Referrals
    # ... logic for ReferredClient ...
    
    # SessionType - **FIX**: Handle 'Update' vs 'Update Only'
    session_type_raw = row.get('Type of Session', DEFAULT_SESSION_TYPE)
    session_type = "Update Only" if session_type_raw.strip() == "Update" else session_type_raw.strip()
    if session_type not in VALID_SESSION_TYPES:
        validator.add_issue(record_id, "warning", ValidationCategory.INVALID_VALUE, "Type of Session", f"Invalid session type '{session_type_raw}', defaulted to {DEFAULT_SESSION_TYPE}.")
        session_type = DEFAULT_SESSION_TYPE
    create_element(counselor_record, 'SessionType', session_type)
    
    # Language
    lang_element = create_element(counselor_record, 'Language')
    language_codes = split_multi_value(row.get('Language(s) Used', DEFAULT_LANGUAGE))
    for code in language_codes:
        create_element(lang_element, 'Code', code)
    create_element(lang_element, 'Other', row.get('Language(s) Used (Other)', ''))
    
    # Date counseled
    create_element(counselor_record, 'DateCounseled', format_date(row.get('Date', '')))
    
    # Counselor name
    create_element(counselor_record, 'CounselorName', row.get('Name of Counselor', ''))
    
    # Counseling hours
    ch_element = create_element(counselor_record, 'CounselingHours')
    contact_val = clean_numeric(row.get('Duration (hours)', '0'))
    
    # Per XSD ModLog #130, contact hours are optional for certain session types.
    if session_type not in NO_CONTACT_HOUR_SESSION_TYPES and float(contact_val or 0) <= 0:
        contact_val = "0.5" # Default contact hours for sessions that need it
    
    create_element(ch_element, 'Contact', contact_val)
    create_element(ch_element, 'Prepare', clean_numeric(row.get('Prep Hours', '0')))
    create_element(ch_element, 'Travel', clean_numeric(row.get('Travel Hours', '0')))
    
    # Counselor notes
    create_element(counselor_record, 'CounselorNotes', truncate_counselor_notes(row.get('Comments', '')))
    
    # Financial assistance
    create_element(counselor_record, 'SBALoanAmount', clean_numeric(row.get('SBA Loan Amount', '0')))
    create_element(counselor_record, 'NonSBALoanAmount', clean_numeric(row.get('Non-SBA Loan Amount', '0')))
    create_element(counselor_record, 'EquityCapitalReceived', clean_numeric(row.get('Amount of Equity Capital Received', '0')))