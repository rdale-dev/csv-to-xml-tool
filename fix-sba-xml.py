#!/usr/bin/env python3
"""
SBA XML Fixer - A utility to fix common XML issues in SBA counseling records.

This script fixes element ordering issues in SBA counseling XML files according to the
SBA_NEXUS_Counseling XSD schema.
"""

import os
import sys
import xml.etree.ElementTree as ET
import argparse
import logging
from datetime import datetime

def setup_logging(log_level=logging.INFO, log_to_file=False):
    """Set up logging configuration."""
    handlers = [logging.StreamHandler()]
    
    if log_to_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"sba_xml_fixer_{timestamp}.log"
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    return logging.getLogger(__name__)

def fix_client_intake_section(xml_file, output_file=None, backup=True):
    """
    Fix the order of elements in the ClientIntake section of SBA counseling XML files.
    
    Args:
        xml_file: Path to the XML file to fix
        output_file: Path to save the fixed XML (default: overwrite original)
        backup: Whether to create a backup of the original file
        
    Returns:
        Path to the fixed XML file
    """
    logger = logging.getLogger(__name__)
    
    if output_file is None:
        output_file = xml_file
    
    # Create backup if requested
    if backup and output_file == xml_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{xml_file}.{timestamp}.bak"
        try:
            import shutil
            shutil.copy2(xml_file, backup_file)
            logger.info(f"Created backup at {backup_file}")
        except Exception as e:
            logger.warning(f"Could not create backup: {str(e)}")
    
    try:
        # Parse the XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Define the correct order of elements in ClientIntake based on XSD schema
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
        
        # Track how many records were fixed
        fixed_count = 0
        records_count = 0
        
        # Process each CounselingRecord
        for counseling_record in root.findall('CounselingRecord'):
            records_count += 1
            client_intake = counseling_record.find('ClientIntake')
            
            if client_intake is not None:
                # Find any ordering issues before fixing
                has_issues = check_element_order(client_intake, client_intake_order)
                
                # Reorder elements in ClientIntake
                reorder_elements(client_intake, client_intake_order)
                
                if has_issues:
                    fixed_count += 1
        
        # Save the fixed XML
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        logger.info(f"Fixed {fixed_count} out of {records_count} counseling records")
        logger.info(f"Saved fixed XML to {output_file}")
        
        return output_file
    
    except Exception as e:
        logger.error(f"Error fixing XML file: {str(e)}")
        return None

def check_element_order(parent, element_order):
    """
    Check if elements are in the correct order.
    
    Args:
        parent: Parent element
        element_order: List of element names in the correct order
        
    Returns:
        Boolean indicating if there are ordering issues
    """
    # Get tags of child elements
    child_tags = [child.tag for child in parent]
    
    # Find elements from order list that exist in the XML
    expected_order = [tag for tag in element_order if tag in child_tags]
    
    # Check if the actual order matches the expected order
    last_index = -1
    for tag in expected_order:
        index = child_tags.index(tag)
        if index < last_index:
            return True  # Order issue found
        last_index = index
    
    return False  # No order issues

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

def add_missing_required_elements(client_intake, record_id):
    """
    Add any missing required elements to ClientIntake.
    
    Args:
        client_intake: ClientIntake element
        record_id: ID of the counseling record
    """
    logger = logging.getLogger(__name__)
    
    # Define required elements and their default values
    required_elements = {
        'CurrentlyInBusiness': 'No',
    }
    
    # Check and add missing elements
    for tag, default_value in required_elements.items():
        if client_intake.find(tag) is None:
            logger.info(f"Record {record_id}: Adding missing required element {tag}")
            ET.SubElement(client_intake, tag).text = default_value

def process_directory(input_dir, output_dir=None, recursive=False, pattern="*.xml"):
    """
    Process all XML files in a directory.
    
    Args:
        input_dir: Input directory containing XML files
        output_dir: Output directory for fixed files (default: same as input)
        recursive: Whether to recursively process subdirectories
        pattern: File pattern to match
        
    Returns:
        Number of files processed
    """
    import glob
    import os
    
    logger = logging.getLogger(__name__)
    logger.info(f"Processing XML files in {input_dir}")
    
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Find XML files
    if recursive:
        files = glob.glob(os.path.join(input_dir, "**", pattern), recursive=True)
    else:
        files = glob.glob(os.path.join(input_dir, pattern))
    
    logger.info(f"Found {len(files)} XML files to process")
    
    # Process each file
    processed_count = 0
    for file_path in files:
        if output_dir:
            # Calculate relative path from input_dir
            rel_path = os.path.relpath(file_path, input_dir)
            # Create output path 
            output_path = os.path.join(output_dir, rel_path)
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        else:
            output_path = file_path
        
        logger.info(f"Processing {file_path}")
        result = fix_client_intake_section(file_path, output_path, backup=(output_dir is None))
        
        if result:
            processed_count += 1
    
    return processed_count

def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description='Fix SBA counseling XML files')
    
    # File/directory selection arguments
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--file', '-f', help='Path to a single XML file to fix')
    input_group.add_argument('--directory', '-d', help='Path to a directory of XML files to fix')
    
    # Output options
    parser.add_argument('--output', '-o', help='Path to save the fixed XML file/directory')
    parser.add_argument('--no-backup', action='store_true', help='Do not create backup of original file')
    
    # Directory processing options
    parser.add_argument('--recursive', '-r', action='store_true', help='Recursively process subdirectories')
    parser.add_argument('--pattern', default="*.xml", help='File pattern for XML files (default: *.xml)')
    
    # Logging options
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                        default='INFO', help='Logging level')
    parser.add_argument('--log-file', action='store_true', help='Save log to file')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    logger = setup_logging(log_level, args.log_file)
    
    try:
        # Process single file
        if args.file:
            logger.info(f"Processing single file: {args.file}")
            result = fix_client_intake_section(args.file, args.output, not args.no_backup)
            if result:
                logger.info(f"Successfully fixed XML file: {result}")
                return 0
            else:
                logger.error("Failed to fix XML file")
                return 1
        
        # Process directory
        elif args.directory:
            logger.info(f"Processing directory: {args.directory}")
            count = process_directory(args.directory, args.output, args.recursive, args.pattern)
            logger.info(f"Successfully processed {count} XML files")
            return 0
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())