"""
CSV to XML conversion utility.
This module handles converting Salesforce counseling data from CSV format to XML.
Updated with improved separation of concerns and fixes for XSD compliance.
"""

import csv
import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime

# Assuming these modules are in the same directory or accessible in the Python path
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

    # Create XML structure
    root = ET.Element('CounselingInformation')
    processed_records = 0
    skipped_records = 0

    # Process each row
    for row_index, row in enumerate(rows, 1):
        record_id = row.get('Contact ID', f"Row_{row_index}")

        # Basic validation to ensure the record is worth processing
        if not validate_record(row, row_index, record_id):
            logger.warning(f"Skipping record {record_id} due to initial validation errors")
            skipped_records += 1
            continue

        try:
            counseling_record = create_element(root, 'CounselingRecord')

            create_element(counseling_record, 'PartnerClientNumber', record_id)

            location = create_element(counseling_record, 'Location')
            create_element(location, 'LocationCode', row.get('LocationCode', DEFAULT_LOCATION_CODE))

            build_client_request_section(counseling_record, row, record_id)
            build_client_intake_section(counseling_record, row, record_id)
            build_counselor_record_section(counseling_record, row, record_id)

            processed_records += 1
            validator.record_processed(success=True)

        except Exception as e:
            logger.error(f"Error processing record {record_id}: {str(e)}", exc_info=True)
            validator.add_issue(
                record_id, "error", ValidationCategory.PROCESSING_ERROR,
                "record", f"Unhandled error processing record: {str(e)}"
            )
            validator.record_processed(success=False)

    # Write the XML tree to the output file
    try:
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")  # For pretty printing
        tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)
        logger.info(f"XML file created successfully with {processed_records} records.")
        if skipped_records > 0:
            logger.info(f"Skipped {skipped_records} records due to validation errors.")
    except Exception as e:
        logger.error(f"Failed to write XML file: {str(e)}")
        validator.add_issue("file", "error", ValidationCategory.FILE_WRITE, "output_file",
                           f"Failed to write XML file: {str(e)}")
        raise


def build_client_request_section(counseling_record, row, record_id):
    """
    Builds the ClientRequest (Part 1) section of the XML.
    """
    client_request = create_element(counseling_record, 'ClientRequest')

    # Client Name, Email, Phone
    client_name = create_element(client_request, 'ClientNamePart1')
    create_element(client_name, 'Last', row.get('Last Name', ''))
    create_element(client_name, 'First', row.get('First Name', ''))
    create_element(client_name, 'Middle', row.get('Middle Name', ''))

    create_element(client_request, 'Email', row.get('Email', ''))
    phone = create_element(client_request, 'PhonePart1')
    create_element(phone, 'Primary', clean_phone_number(row.get('Contact: Phone', '')))
    create_element(phone, 'Secondary', '')

    # Address
    address = create_element(client_request, 'AddressPart1')
    create_element(address, 'Street1', row.get('Mailing Street', ''))
    create_element(address, 'Street2', '')
    create_element(address, 'City', row.get('Mailing City', ''))
    create_element(address, 'State', standardize_state_name(row.get('Mailing State/Province', '')))

    zip_full = str(row.get('Mailing Zip/Postal Code', '')).strip()
    zip_5digit_match = re.match(r'^\d{5}', zip_full)
    zip_5digit = zip_5digit_match.group(0) if zip_5digit_match else ''
    if not zip_5digit and zip_full:
        validator.add_issue(record_id, "warning", ValidationCategory.INVALID_FORMAT, "Mailing Zip/Postal Code", f"Could not parse 5-digit ZIP from '{zip_full}'.")
    create_element(address, 'ZipCode', zip_5digit)
    create_element(address, 'Zip4Code', '')

    country = create_element(address, 'Country')
    create_element(country, 'Code', standardize_country_code(row.get('Mailing Country', 'US')))

    # Agreement and Signature
    create_element(client_request, 'SurveyAgreement', row.get('Agree to Impact Survey', 'No'))

    signature = create_element(client_request, 'ClientSignature')
    create_element(signature, 'Date', format_date(row.get('Client Signature - Date', '')))
    signature_onfile = row.get('Client Signature(On File)', 'No')
    create_element(signature, 'OnFile', 'Yes' if signature_onfile in ['1', 1] else 'No')


def build_client_intake_section(counseling_record, row, record_id):
    """
    Builds the ClientIntake (Part 2) section of the XML, ensuring correct element order.
    """
    client_intake = create_element(counseling_record, 'ClientIntake')

    # 1. Race
    race_element = create_element(client_intake, 'Race')
    race_codes = split_multi_value(row.get('Race', ''))
    if race_codes:
        for code in race_codes:
            create_element(race_element, 'Code', code)
    else:
        create_element(race_element, 'Code', 'Prefer not to say')
        validator.add_issue(record_id, "warning", ValidationCategory.MISSING_FIELD, "Race", "Race missing, defaulted to 'Prefer not to say'.")

    # 2. Ethnicity
    ethnicity_csv = row.get('Ethnicity:', '').strip() # Note the colon in the sample header
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
            validator.add_issue(record_id, "error", ValidationCategory.MISSING_REQUIRED, "BranchOfService", f"BranchOfService required for MilitaryStatus '{military_status_csv}' but is missing/invalid.")

    # 7. Media
    media_codes = split_multi_value(row.get('What Prompted you to contact us?', ''))
    media_other = row.get('Internet (specify)', '').strip()
    if media_codes or media_other:
        media = create_element(client_intake, 'Media')
        for code in media_codes:
            create_element(media, 'Code', code)
        if media_other:
            create_element(media, 'Other', media_other)

    # 8. Internet (Note: This is a distinct field from Media/Other)
    # Use a specific column if it exists, otherwise this element is omitted.
    internet_usage = row.get('InternetUsage', '').strip() # Example: Assumes a column named 'InternetUsage'
    if internet_usage:
        create_element(client_intake, 'Internet', internet_usage)

    # 9. CurrentlyInBusiness
    in_business_val = row.get('Currently In Business?', DEFAULT_BUSINESS_STATUS)
    create_element(client_intake, 'CurrentlyInBusiness', in_business_val)

    # 10. CurrentlyExporting
    exporting_val = row.get('Are you currently exporting?(old)', DEFAULT_BUSINESS_STATUS)
    create_element(client_intake, 'CurrentlyExporting', exporting_val)

    # 11. CompanyName
    create_element(client_intake, 'CompanyName', row.get('Account Name', ''))

    # 12. BusinessType
    create_element(client_intake, 'BusinessType', row.get('Type of Business', ''))

    # 13. BusinessOwnership
    bo_element = create_element(client_intake, 'BusinessOwnership')
    female_ownership_val = clean_percentage(row.get('Business Ownership - % Female(old)', '0'))
    create_element(bo_element, 'Female', female_ownership_val)

    # 14. ConductingBusinessOnline
    create_element(client_intake, 'ConductingBusinessOnline', row.get('Conduct Business Online?', DEFAULT_BUSINESS_STATUS))

    # 15. ClientIntake_Certified8a
    create_element(client_intake, 'ClientIntake_Certified8a', row.get('8(a) Certified?(old)', DEFAULT_BUSINESS_STATUS))

    # 16. TotalNumberOfEmployees
    create_element(client_intake, 'TotalNumberOfEmployees', clean_numeric(row.get('Total Number of Employees', '0')))

    # 17. NumberOfEmployeesInExportingBusiness
    create_element(client_intake, 'NumberOfEmployeesInExportingBusiness', '0') # Defaulting to '0' as not in sample

    # 18. ClientAnnualIncomePart2
    income_part2 = create_element(client_intake, 'ClientAnnualIncomePart2')
    create_element(income_part2, 'GrossRevenues', clean_numeric(row.get('Gross Revenues/Sales', '0')))
    create_element(income_part2, 'ProfitLoss', clean_numeric(row.get('Profits/Losses', '0')))
    create_element(income_part2, 'ExportGrossRevenuesOrSales', '0')

    # 19. LegalEntity
    if in_business_val.lower() == 'yes':
        le_element = create_element(client_intake, 'LegalEntity')
        le_codes = split_multi_value(row.get('Legal Entity of Business', ''))
        le_other = row.get('Other legal entity (specify)', '').strip()
        if le_codes:
            for code in le_codes: create_element(le_element, 'Code', code)
        elif le_other:
            create_element(le_element, 'Code', 'Other')
        else:
            validator.add_issue(record_id, "error", ValidationCategory.MISSING_REQUIRED, "LegalEntity", "Client is in business, but Legal Entity is missing.")
            create_element(le_element, 'Code', 'Other') # Default to prevent structural error
        if le_other:
            create_element(le_element, 'Other', le_other)

    # 20. Rural_vs_Urban
    # Assumes mapping from county or a direct CSV column exists.
    rural_urban_val = row.get('Rural_vs_Urban', DEFAULT_URBAN_RURAL)
    create_element(client_intake, 'Rural_vs_Urban', rural_urban_val)

    # 21. FIPS_Code
    if rural_urban_val.lower() in ['rural', 'urban']:
        fips_code = row.get('FIPS_Code', '').strip()
        if fips_code:
            create_element(client_intake, 'FIPS_Code', fips_code)
        else:
            validator.add_issue(record_id, "error", ValidationCategory.MISSING_REQUIRED, "FIPS_Code", f"FIPS Code required for Rural/Urban status '{rural_urban_val}' but is missing.")

    # 22. CounselingSeeking
    cs_codes = split_multi_value(row.get('Nature of the Counseling Seeking?', ''))
    cs_other = row.get('Nature of the Counseling Seeking - Other Detail', '').strip()
    if cs_codes or cs_other:
        cs_element = create_element(client_intake, 'CounselingSeeking')
        is_other_present = any(c.lower() == 'other' for c in cs_codes)
        for code in cs_codes: create_element(cs_element, 'Code', code)
        if is_other_present and not cs_other:
            validator.add_issue(record_id, "error", ValidationCategory.MISSING_REQUIRED, "CounselingSeeking/Other", "CounselingSeeking is 'Other' but detail text is missing.")
        create_element(cs_element, 'Other', cs_other)


def build_counselor_record_section(counseling_record, row, record_id):
    """
    Builds the CounselorRecord (Part 3) section of the XML.
    """
    counselor_record = create_element(counseling_record, 'CounselorRecord')

    # Session Info
    create_element(counselor_record, 'PartnerSessionNumber', row.get('Activity ID', ''))
    create_element(counselor_record, 'FundingSource', '')

    # Contact Info (Optional in XSD, but populated from client data per original script)
    create_element(counselor_record, 'ClientNamePart3', type="PersonType") # This seems to be a mistake in the original logic, should likely be CounselorName, but following original structure.
    create_element(counselor_record, 'Email', row.get('Email', ''))
    create_element(counselor_record, 'PhonePart3', type="PhoneType") # This also seems like a mistake.

    # **FIX**: Fully populate the AddressPart3 block to resolve "City is required" errors.
    address_part3 = create_element(counselor_record, 'AddressPart3')
    create_element(address_part3, 'Street1', row.get('Mailing Street', ''))
    create_element(address_part3, 'Street2', '')
    create_element(address_part3, 'City', row.get('Mailing City', ''))
    create_element(address_part3, 'State', standardize_state_name(row.get('Mailing State/Province', '')))

    zip_full_p3 = str(row.get('Mailing Zip/Postal Code', '')).strip()
    zip_5digit_match_p3 = re.match(r'^\d{5}', zip_full_p3)
    zip_5digit_p3 = zip_5digit_match_p3.group(0) if zip_5digit_match_p3 else ''
    create_element(address_part3, 'ZipCode', zip_5digit_p3)
    create_element(address_part3, 'Zip4Code', '')

    country_p3 = create_element(address_part3, 'Country')
    create_element(country_p3, 'Code', standardize_country_code(row.get('Mailing Country', 'US')))

    # Business Status & Impact
    create_element(counselor_record, 'VerifiedToBeInBusiness', 'Undetermined')
    create_element(counselor_record, 'ReportableImpact', row.get('Reportable Impact', DEFAULT_BUSINESS_STATUS))
    create_element(counselor_record, 'DateOfReportableImpact', format_date(row.get('Reportable Impact Date', '')))
    create_element(counselor_record, 'CurrentlyExporting', DEFAULT_BUSINESS_STATUS)

    business_start_date = format_date(row.get('Business Start Date', '')) or format_date(row.get('Date Started (Meeting)', ''))
    if business_start_date:
        create_element(counselor_record, 'BusinessStartDatePart3', business_start_date)

    # Meeting-specific numbers
    create_element(counselor_record, 'TotalNumberOfEmployees', clean_numeric(row.get('Total No. of Employees (Meeting)', row.get('Total Number of Employees', '0'))))
    create_element(counselor_record, 'NumberOfEmployeesInExportingBusiness', '0')

    income_part3 = create_element(counselor_record, 'ClientAnnualIncomePart3')
    create_element(income_part3, 'GrossRevenues', clean_numeric(row.get('Gross Revenues/Sales (Meeting)', row.get('Gross Revenues/Sales', '0'))))
    create_element(income_part3, 'ProfitLoss', clean_numeric(row.get('Profit & Loss (Meeting)', row.get('Profits/Losses', '0'))))
    create_element(income_part3, 'ExportGrossRevenuesOrSales', '0')
    create_element(income_part3, 'GrowthIndicator', '')

    # Counseling Details
    cp_element = create_element(counselor_record, 'CounselingProvided')
    provided_codes = split_multi_value(row.get('Services Provided', 'Business Start-up/Preplanning'))
    for code in provided_codes:
        create_element(cp_element, 'Code', code)

    # Session Type
    session_type_raw = row.get('Type of Session', DEFAULT_SESSION_TYPE)
    session_type = "Update Only" if session_type_raw.strip() == "Update" else session_type_raw.strip()
    if session_type not in VALID_SESSION_TYPES:
        validator.add_issue(record_id, "warning", ValidationCategory.INVALID_VALUE, "SessionType", f"Invalid session type '{session_type_raw}', defaulted.")
        session_type = DEFAULT_SESSION_TYPE
    create_element(counselor_record, 'SessionType', session_type)

    # Language
    lang_element = create_element(counselor_record, 'Language')
    for code in split_multi_value(row.get('Language(s) Used', DEFAULT_LANGUAGE)):
        create_element(lang_element, 'Code', code)
    create_element(lang_element, 'Other', row.get('Language(s) Used (Other)', ''))

    create_element(counselor_record, 'DateCounseled', format_date(row.get('Date', '')))
    create_element(counselor_record, 'CounselorName', row.get('Name of Counselor', ''))

    # Hours
    ch_element = create_element(counselor_record, 'CounselingHours')
    contact_val = clean_numeric(row.get('Duration (hours)', '0'))
    if session_type not in NO_CONTACT_HOUR_SESSION_TYPES and float(contact_val or 0) <= 0:
        contact_val = "0.5"
    create_element(ch_element, 'Contact', contact_val)
    create_element(ch_element, 'Prepare', clean_numeric(row.get('Prep Hours', '0')))
    create_element(ch_element, 'Travel', clean_numeric(row.get('Travel Hours', '0')))

    create_element(counselor_record, 'CounselorNotes', truncate_counselor_notes(row.get('Comments', '')))

    # Financial Assistance Received
    create_element(counselor_record, 'SBALoanAmount', clean_numeric(row.get('SBA Loan Amount', '0')))
    create_element(counselor_record, 'NonSBALoanAmount', clean_numeric(row.get('Non-SBA Loan Amount', '0')))
    create_element(counselor_record, 'EquityCapitalReceived', clean_numeric(row.get('Amount of Equity Capital Received', '0')))
```