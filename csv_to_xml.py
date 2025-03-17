"""
CSV to XML conversion utility.
This module handles converting Salesforce counseling data from CSV format to XML.
Updated with improved separation of concerns.
"""

import csv
import xml.etree.ElementTree as ET
import os
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
    DEFAULT_BUSINESS_STATUS, DEFAULT_LANGUAGE, ValidationCategory
)

# Import default logger and validator (will be overridden in create_xml_from_csv)
from logging_util import logger
from validation_report import validator


def create_element(parent, element_name, element_text=None):
    """
    Helper function to create an XML element and add it to a parent element.
    
    Args:
        parent: The parent XML element
        element_name: Name of the new element
        element_text: Optional text content for the new element
        
    Returns:
        The newly created XML element
    """
    element = ET.SubElement(parent, element_name)
    if element_text is not None:
        element.text = str(element_text)
    return element


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
    create_element(address, 'ZipCode', row.get('Mailing Zip/Postal Code', ''))
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
    
    Args:
        counseling_record: The parent XML element
        row: Dictionary of field values
        record_id: ID of the record
    """
    client_intake = create_element(counseling_record, 'ClientIntake')
    
    # Race information (multi-value field)
    race = create_element(client_intake, 'Race')
    race_codes = split_multi_value(row.get('Race', ''))
    for code in race_codes:
        create_element(race, 'Code', code)
    create_element(race, 'SelfDescribedRace', '')
    
    # Demographics
    ethnicity = row.get('Ethnicity::', 'Prefer not to say')
    create_element(client_intake, 'Ethnicity', ethnicity)
    
    # Convert Gender to Sex (XSD requirement)
    sex_value = map_gender_to_sex(row.get('Gender', ''))
    if sex_value:
        create_element(client_intake, 'Sex', sex_value)
    
    disability = row.get('Disability', 'Prefer not to say')
    create_element(client_intake, 'Disability', disability)
    
    # Military information
    military_status = row.get('Veteran Status', 'Prefer not to say')
    create_element(client_intake, 'MilitaryStatus', military_status)
    
    # Add Branch of Service only for military personnel
    if military_status not in ['Prefer not to say', 'No military service']:
        branch = row.get('Branch Of Service', 'Prefer not to say')
        create_element(client_intake, 'BranchOfService', branch)
    
    # Referral information (Media)
    media_codes = split_multi_value(row.get('What Prompted you to contact us?', ''))
    if media_codes or row.get('Internet (specify)'):
        media = create_element(client_intake, 'Media')
        for code in media_codes:
            create_element(media, 'Code', code)
        media_other = row.get('Internet (specify)', '')
        if media_other:
            create_element(media, 'Other', media_other)
    
    # Internet usage
    create_element(client_intake, 'Internet', row.get('ClientIntake_Internet', ''))
    
    # Business information
    currently_in_business = row.get('Currently In Business?', DEFAULT_BUSINESS_STATUS)
    create_element(client_intake, 'CurrentlyInBusiness', currently_in_business)
    
    currently_exporting = row.get('Are you currently exporting?', DEFAULT_BUSINESS_STATUS)
    create_element(client_intake, 'CurrentlyExporting', currently_exporting)
    
    company_name = row.get('Account Name', '')
    create_element(client_intake, 'CompanyName', company_name)
    
    business_type = row.get('Type of Business', '')
    create_element(client_intake, 'BusinessType', business_type)
    
    # Business ownership
    business_ownership = create_element(client_intake, 'BusinessOwnership')
    female_ownership = clean_percentage(row.get('Business Ownership - % Female', '0'))
    create_element(business_ownership, 'Female', female_ownership)
    
    # Business operations
    conducting_online = row.get('Conduct Business Online?', DEFAULT_BUSINESS_STATUS)
    create_element(client_intake, 'ConductingBusinessOnline', conducting_online)
    
    certified_8a = row.get('8(a) Certified?', DEFAULT_BUSINESS_STATUS)
    create_element(client_intake, 'ClientIntake_Certified8a', certified_8a)
    
    # Employee and financial information
    employees = row.get('Total Number of Employees', '0')
    create_element(client_intake, 'TotalNumberOfEmployees', clean_numeric(employees))
    create_element(client_intake, 'NumberOfEmployeesInExportingBusiness', '0')
    
    # Financial information
    client_annual_income = create_element(client_intake, 'ClientAnnualIncomePart2')
    gross_revenue = row.get('Gross Revenues/Sales', '0')
    create_element(client_annual_income, 'GrossRevenues', clean_numeric(gross_revenue))
    
    profit_loss = row.get('Profits/Losses', '0')
    create_element(client_annual_income, 'ProfitLoss', clean_numeric(profit_loss))
    
    create_element(client_annual_income, 'ExportGrossRevenuesOrSales', '0')
    
    # Legal entity information
    legal_entity_codes = split_multi_value(row.get('Legal Entity of Business', ''))
    if legal_entity_codes or row.get('Other legal entity (specify)'):
        legal_entity = create_element(client_intake, 'LegalEntity')
        for code in legal_entity_codes:
            create_element(legal_entity, 'Code', code)
        legal_entity_other = row.get('Other legal entity (specify)', '')
        if legal_entity_other:
            create_element(legal_entity, 'Other', legal_entity_other)
    
    # Rural/Urban status
    create_element(client_intake, 'Rural_vs_Urban', row.get('ClientIntake_RuralVsUrban', 'Undetermined'))
    
    # Add FIPS Code if Rural or Urban
    if row.get('ClientIntake_RuralVsUrban') in ['Rural', 'Urban'] and row.get('ClientIntake_FIPSCode'):
        create_element(client_intake, 'FIPS_Code', row.get('ClientIntake_FIPSCode', ''))
    
    # Counseling seeking information
    counseling_seeking_codes = split_multi_value(row.get('Nature of the Counseling Seeking?', ''))
    if counseling_seeking_codes:
        counseling_seeking = create_element(client_intake, 'CounselingSeeking')
        for code in counseling_seeking_codes:
            create_element(counseling_seeking, 'Code', code)
        create_element(counseling_seeking, 'Other', '')


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
    session_number = row.get('Activity ID', '')
    create_element(counselor_record, 'PartnerSessionNumber', session_number)
    create_element(counselor_record, 'FundingSource', '')
    
    # Counselor name and contact information
    counselor_name = create_element(counselor_record, 'ClientNamePart3')
    create_element(counselor_name, 'Last', row.get('Last Name', ''))
    create_element(counselor_name, 'First', row.get('First Name', ''))
    create_element(counselor_name, 'Middle', row.get('Middle Name', ''))
    
    # Contact information
    create_element(counselor_record, 'Email', row.get('Email', ''))
    
    phone = create_element(counselor_record, 'PhonePart3')
    create_element(phone, 'Primary', clean_phone_number(row.get('Contact: Phone', '')))
    create_element(phone, 'Secondary', '')
    
    # Address information
    address = create_element(counselor_record, 'AddressPart3')
    create_element(address, 'Street1', row.get('Mailing Street', ''))
    create_element(address, 'Street2', '')
    create_element(address, 'City', row.get('Mailing City', ''))
    state_value = row.get('Mailing State/Province', '')
    standardized_state = standardize_state_name(state_value)
    create_element(address, 'State', standardized_state)
    create_element(address, 'ZipCode', row.get('Mailing Zip/Postal Code', ''))
    create_element(address, 'Zip4Code', '')
    
    # Country with standardization
    country = create_element(address, 'Country')
    country_value = row.get('Mailing Country', 'US')
    standardized_country = standardize_country_code(country_value)
    create_element(country, 'Code', standardized_country)
    
    create_element(address, 'PostalCode', '')
    create_element(address, 'StateOrProvince', '')
    
    # Business verification
    create_element(counselor_record, 'VerifiedToBeInBusiness', 'Undetermined')
    create_element(counselor_record, 'ReportableImpact', DEFAULT_BUSINESS_STATUS)
    create_element(counselor_record, 'DateOfReportableImpact', '')
    create_element(counselor_record, 'CurrentlyExporting', DEFAULT_BUSINESS_STATUS)
    
    # Business start date - use Business Start Date with fallback to Date Started (Meeting)
    business_start_date = format_date(row.get('Business Start Date', ''))
    if not business_start_date:
        business_start_date = format_date(row.get('Date Started (Meeting)', ''))
        
    if business_start_date:
        create_element(counselor_record, 'BusinessStartDatePart3', business_start_date)
    
    # Employee information
    employee_count = clean_numeric(row.get('Total No. of Employees (Meeting)', 
                                    row.get('Total Number of Employees', '0')))
    create_element(counselor_record, 'TotalNumberOfEmployees', employee_count)
    create_element(counselor_record, 'NumberOfEmployeesInExportingBusiness', '0')
    
    # Financial information
    client_annual_income = create_element(counselor_record, 'ClientAnnualIncomePart3')
    gross_revenues = clean_numeric(row.get('Gross Revenues/Sales (Meeting)', 
                                   row.get('Gross Revenues/Sales', '0')))
    create_element(client_annual_income, 'GrossRevenues', gross_revenues)
    
    profit_loss = clean_numeric(row.get('Profit & Loss (Meeting)', 
                               row.get('Profits/Losses', '0')))
    create_element(client_annual_income, 'ProfitLoss', profit_loss)
    
    create_element(client_annual_income, 'ExportGrossRevenuesOrSales', '0')
    create_element(client_annual_income, 'GrowthIndicator', '')
    
    # Certifications
    certification_codes = split_multi_value(row.get('Certifications (SDB, HUBZONE, etc)', ''))
    if certification_codes or row.get('Other Certifications'):
        certifications = create_element(counselor_record, 'Certifications')
        for code in certification_codes:
            create_element(certifications, 'Code', code)
        cert_other = row.get('Other Certifications', '')
        if cert_other:
            create_element(certifications, 'Other', cert_other)
    
    # SBA Financial Assistance
    sba_financial_codes = split_multi_value(row.get('SBA Financial Assistance', ''))
    if sba_financial_codes or row.get('Other SBA Financial Assistance'):
        sba_financial = create_element(counselor_record, 'SBAFinancialAssistance')
        for code in sba_financial_codes:
            create_element(sba_financial, 'Code', code)
        sba_other = row.get('Other SBA Financial Assistance', '')
        if sba_other:
            create_element(sba_financial, 'Other', sba_other)
    
    # Counseling provided (mandatory)
    counseling_provided = create_element(counselor_record, 'CounselingProvided')
    provided_codes = split_multi_value(row.get('Services Provided', 'Business Start-up/Preplanning'))
    for code in provided_codes:
        create_element(counseling_provided, 'Code', code)
    create_element(counseling_provided, 'Other', '')
    
    # Referrals
    referral_codes = split_multi_value(row.get('Referred Client to', ''))
    if referral_codes or row.get('Other (Referred Client to)'):
        referred_client = create_element(counselor_record, 'ReferredClient')
        for code in referral_codes:
            create_element(referred_client, 'Code', code)
        ref_other = row.get('Other (Referred Client to)', '')
        if ref_other:
            create_element(referred_client, 'Other', ref_other)
    
    # Session information
    session_type = row.get('Type of Session', 'Telephone')
    create_element(counselor_record, 'SessionType', session_type)
    
    # Language information
    language_codes = split_multi_value(row.get('Language(s) Used', DEFAULT_LANGUAGE))
    language = create_element(counselor_record, 'Language')
    for code in language_codes:
        create_element(language, 'Code', code)
    lang_other = row.get('Language(s) Used (Other)', '')
    if lang_other:
        create_element(language, 'Other', lang_other)
    
    # Date counseled
    date_counseled = format_date(row.get('Date', ''))
    if date_counseled:
        create_element(counselor_record, 'DateCounseled', date_counseled)
    
    # Counselor name
    counselor_name_value = row.get('Name of Counselor', '')
    create_element(counselor_record, 'CounselorName', counselor_name_value)
    
    # Counseling hours
    counseling_hours = create_element(counselor_record, 'CounselingHours')
    contact_value = clean_numeric(row.get('Duration (hours)', '0'))
    prepare_value = clean_numeric(row.get('Prep Hours', '0'))
    travel_value = clean_numeric(row.get('Travel Hours', '0'))
    
    # Default contact hours for non-prepare-only sessions
    if session_type not in NO_CONTACT_HOUR_SESSION_TYPES and float(contact_value or 0) <= 0:
        contact_value = "0.5"
    
    create_element(counseling_hours, 'Contact', contact_value)
    create_element(counseling_hours, 'Prepare', prepare_value)
    create_element(counseling_hours, 'Travel', travel_value)
    
    # Counselor notes with truncation
    counselor_notes = truncate_counselor_notes(row.get('Comments', ''))
    create_element(counselor_record, 'CounselorNotes', counselor_notes)
    
    # Financial assistance
    create_element(counselor_record, 'SBALoanAmount', clean_numeric(row.get('SBA Loan Amount', '0')))
    create_element(counselor_record, 'NonSBALoanAmount', clean_numeric(row.get('Non-SBA Loan Amount', '0')))
    create_element(counselor_record, 'EquityCapitalReceived', 
                  clean_numeric(row.get('Amount of Equity Capital Received', '0')))  
