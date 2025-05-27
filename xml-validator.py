"""
XML validator and fixer utility for SBA Counseling Information forms.
This module helps validate and fix common XML structure issues.
"""

import os
import sys
import xml.etree.ElementTree as ET
from lxml import etree
import logging
import re

logger = logging.getLogger(__name__)

def setup_logging(log_level=logging.INFO):
    """Set up logging configuration."""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def validate_against_xsd(xml_file, xsd_file):
    """
    Validate XML against an XSD schema.
    
    Args:
        xml_file: Path to the XML file
        xsd_file: Path to the XSD schema file
        
    Returns:
        Tuple (is_valid, errors)
    """
    try:
        # Parse the XSD schema
        xmlschema_doc = etree.parse(xsd_file)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        
        # Parse the XML file
        xml_doc = etree.parse(xml_file)
        
        # Validate
        is_valid = xmlschema.validate(xml_doc)
        
        # Get validation errors
        errors = []
        if not is_valid:
            for error in xmlschema.error_log:
                errors.append(f"Line {error.line}: {error.message}")
        
        return is_valid, errors
    except Exception as e:
        return False, [f"Validation error: {str(e)}"]

def extract_validation_details(error_message):
    """
    Extract element names and expected elements from a validation error message.
    
    Args:
        error_message: The validation error message
        
    Returns:
        Tuple (invalid_element, expected_elements)
    """
    invalid_match = re.search(r"Invalid content was found starting with element '([^']+)'", error_message)
    expected_match = re.search(r"One of '{([^}]+)}' is expected", error_message)
    
    invalid_element = invalid_match.group(1) if invalid_match else None
    expected_elements = expected_match.group(1).split(', ') if expected_match else []
    
    return invalid_element, expected_elements

def fix_client_intake_element_order(xml_file, output_file=None):
    """
    Fix the order of elements in the ClientIntake section according to the XSD schema.
    
    Args:
        xml_file: Path to the XML file
        output_file: Path to save the fixed XML file (if None, will modify the original)
        
    Returns:
        Boolean indicating success
    """
    if output_file is None:
        output_file = xml_file
    
    try:
        # Parse the XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Define the correct order of elements in ClientIntake
        client_intake_order = [
            'Race', 'Ethnicity', 'Sex', 'Disability', 'MilitaryStatus', 
            'BranchOfService', 'Media', 'Internet', 'CurrentlyInBusiness', 
            'CurrentlyExporting', 'CompanyName', 'BusinessType', 
            'BusinessOwnership', 'ConductingBusinessOnline', 
            'ClientIntake_Certified8a', 'Employee_Owned', 'TotalNumberOfEmployees',
            'NumberOfEmployeesInExportingBusiness', 'ClientAnnualIncomePart2',
            'LegalEntity', 'Rural_vs_Urban', 'FIPS_Code', 'CounselingSeeking',
            'ExportCountries'
        ]
        
        # Process each CounselingRecord
        for counseling_record in root.findall('CounselingRecord'):
            client_intake = counseling_record.find('ClientIntake')
            if client_intake is not None:
                # Reorder elements in ClientIntake
                reorder_elements(client_intake, client_intake_order)
        
        # Save the fixed XML
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        return True
    except Exception as e:
        logger.error(f"Error fixing XML file: {str(e)}")
        return False

def reorder_elements(parent, element_order):
    """
    Reorder child elements according to the specified order.
    
    Args:
        parent: Parent element
        element_order: List of element names in the correct order
    """
    # Create a dictionary to store elements by tag name
    elements = {}
    for child in list(parent):
        tag = child.tag
        if tag in elements:
            # If we already have this tag, it's a list of elements
            if isinstance(elements[tag], list):
                elements[tag].append(child)
            else:
                elements[tag] = [elements[tag], child]
        else:
            elements[tag] = child
        
        # Remove the child from the parent
        parent.remove(child)
    
    # Add elements back in the correct order
    for tag in element_order:
        if tag in elements:
            if isinstance(elements[tag], list):
                # Add all elements with this tag
                for element in elements[tag]:
                    parent.append(element)
            else:
                # Add the single element
                parent.append(elements[tag])
    
    # Add any remaining elements that weren't in the order list
    for tag, element in elements.items():
        if tag not in element_order:
            if isinstance(element, list):
                for item in element:
                    parent.append(item)
            else:
                parent.append(element)

def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='XML Validator and Fixer')
    parser.add_argument('--xml', required=True, help='Path to the XML file')
    parser.add_argument('--xsd', help='Path to the XSD schema file')
    parser.add_argument('--output', help='Path to save the fixed XML file')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                        default='INFO', help='Logging level')
    parser.add_argument('--fix', action='store_true', help='Fix the XML file')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    logger = setup_logging(log_level)
    
    # Validate XML against XSD if schema file is provided
    if args.xsd:
        logger.info(f"Validating {args.xml} against {args.xsd}...")
        is_valid, errors = validate_against_xsd(args.xml, args.xsd)
        
        if is_valid:
            logger.info("XML is valid!")
        else:
            logger.error(f"XML is not valid. Found {len(errors)} errors:")
            for i, error in enumerate(errors, 1):
                logger.error(f"Error {i}: {error}")
                
                # Extract details from error message
                invalid_element, expected_elements = extract_validation_details(error)
                if invalid_element and expected_elements:
                    logger.info(f"Invalid element: '{invalid_element}'")
                    logger.info(f"Expected elements: {', '.join(expected_elements)}")
    
    # Fix the XML file if requested
    if args.fix:
        output_file = args.output if args.output else args.xml
        logger.info(f"Fixing XML file and saving to {output_file}...")
        
        if fix_client_intake_element_order(args.xml, output_file):
            logger.info("XML file fixed successfully!")
        else:
            logger.error("Failed to fix XML file.")
    
if __name__ == "__main__":
    main()