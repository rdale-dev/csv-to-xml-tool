"""
Main module for CSV to XML conversion utility.
This module orchestrates the conversion process by importing and calling
the functions from the other modules.
"""

import os
import argparse
import logging
import sys
from datetime import datetime

from csv_to_xml import create_xml_from_csv
from data_cleaning import standardize_country_code, standardize_state_name
from data_validation import analyze_csv_data
from logging_util import ConversionLogger
from validation_report import ValidationTracker


def test_state_standardization():
    """Test function to verify state standardization works correctly."""
    test_values = [
        "AL", "al", "Alabama", "alabama", " AL ", 
        "IA", "ia", "Iowa", "iowa", " IA ",
        "NY", "ny", "New York", "new york", " NY ",
        "CA", "ca", "California", "california", " CA ",
        "TX", "tx", "Texas", "texas", " TX ",
        "UnknownState"  # Should return as is
    ]
    
    logger.info("Testing state standardization:")
    for value in test_values:
        standardized = standardize_state_name(value)
        logger.debug(f"  '{value}' -> '{standardized}'")
    
    # Return True if everything looks good
    return True

def test_country_standardization():
    """Test function to verify country standardization works correctly."""
    test_values = [
        "US", "USA", "U.S.", "U.S.A.", "United States", "United States of America",
        "us", "usa", " US ", "America",
        "CA", "CAN", "Canada",
        "MX", "MEX", "Mexico",
        "UK", "GB", "GBR", "Great Britain", "United Kingdom",
    ]
    
    logger.info("Testing country standardization:")
    for value in test_values:
        standardized = standardize_country_code(value)
        logger.debug(f"  '{value}' -> '{standardized}'")
    
    # Return True if everything looks good
    return True

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='CSV to XML Conversion Utility')
    parser.add_argument('--input', '-i', help='Path to the input CSV file')
    parser.add_argument('--output', '-o', help='Path to the output XML file (optional)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                        default='INFO', help='Logging level')
    parser.add_argument('--report-dir', default='reports',
                        help='Directory to save validation reports')
    parser.add_argument('--log-dir', default='logs',
                        help='Directory to save log files')
    parser.add_argument('--test-countries', action='store_true',
                        help='Run country standardization test')
    parser.add_argument('--test-states', action='store_true',
                        help='Run state standardization test')
    parser.add_argument('--analyze-only', action='store_true',
                        help='Only analyze the CSV without conversion')
    
    return parser.parse_args()

def analyze_csv_file(csv_file_path, validator):
    """
    Analyzes a CSV file for potential issues without performing conversion.
    
    Args:
        csv_file_path: Path to the CSV file
        validator: Validation tracker instance
    """
    import csv
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            rows = list(csv_reader)
            logger.info(f"Successfully read CSV file with {len(rows)} records")
    except Exception as e:
        logger.error(f"Failed to read CSV file: {str(e)}")
        return
    
    # Analyze the data
    analysis = analyze_csv_data(rows)
    
    # Print analysis results
    logger.info("CSV Analysis Results:")
    logger.info(f"Total records: {analysis['row_count']}")
    logger.info(f"Records missing Contact ID: {analysis['missing_contact_id']}")
    logger.info(f"Records missing name information: {analysis['missing_names']}")
    logger.info(f"Records with invalid dates: {analysis['invalid_dates']}")
    
    # Print country analysis
    logger.info("Country values found in data:")
    for country, count in sorted(analysis['country_values'].items()):
        standardized = standardize_country_code(country)
        
        if standardized != country:
            logger.info(f"  '{country}' ({count} occurrences) - will be standardized to '{standardized}'")
        else:
            logger.info(f"  '{country}' ({count} occurrences)")
    
    # Create a simple report
    report_path = os.path.join(args.report_dir, f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    try:
        os.makedirs(args.report_dir, exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(f"CSV Analysis Report for {csv_file_path}\n")
            f.write(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Total records: {analysis['row_count']}\n")
            f.write(f"Records missing Contact ID: {analysis['missing_contact_id']}\n")
            f.write(f"Records missing name information: {analysis['missing_names']}\n")
            f.write(f"Records with invalid dates: {analysis['invalid_dates']}\n\n")
            
            f.write("Country values found in data:\n")
            for country, count in sorted(analysis['country_values'].items()):
                standardized = standardize_country_code(country)
                if standardized != country:
                    f.write(f"  '{country}' ({count} occurrences) - will be standardized to '{standardized}'\n")
                else:
                    f.write(f"  '{country}' ({count} occurrences)\n")
                    
        logger.info(f"Analysis report saved to: {report_path}")
    except Exception as e:
        logger.error(f"Failed to write analysis report: {str(e)}")

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    global args, logger
    args = parse_arguments()
    
    # Initialize logging
    log_level = getattr(logging, args.log_level)
    logger = ConversionLogger(log_level=log_level, log_dir=args.log_dir)
    
    # Initialize validation tracker
    validator = ValidationTracker()
    
    logger.info("CSV to XML Conversion Utility")
    logger.info("-----------------------------")
    
    # Run country standardization test if requested
    if args.test_countries:
        logger.info("Running country standardization test...")
        test_country_standardization()
        logger.info("Test completed.")
        return
    
    # Add state standardization test option
    if getattr(args, 'test_states', False):
        logger.info("Running state standardization test...")
        test_state_standardization()
        logger.info("Test completed.")
        return
    
    # Get input file path
    csv_file_path = args.input
    if not csv_file_path:
        csv_file_path = input("Enter the path to your CSV file: ")
    
    if not os.path.exists(csv_file_path):
        logger.error(f"Input file not found: {csv_file_path}")
        return
    
    # If analyze only mode, just analyze the file
    if args.analyze_only:
        logger.info(f"Analyzing CSV file: {csv_file_path}")
        analyze_csv_file(csv_file_path, validator)
        return
    
    # Determine output file path
    if args.output:
        xml_file_path = args.output
    else:
        # Use same directory as input file with timestamped name
        csv_directory = os.path.dirname(csv_file_path)
        if not csv_directory:
            csv_directory = "."
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(csv_file_path)
        base_name = os.path.splitext(filename)[0]
        xml_file_path = os.path.join(csv_directory, f"{base_name}_{timestamp}.xml")
    
    # Ensure the output directory exists
    output_dir = os.path.dirname(xml_file_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Perform the conversion
    logger.info(f"Converting {csv_file_path} to XML...")
    try:
        create_xml_from_csv(csv_file_path, xml_file_path, logger, validator)
        logger.info(f"XML file created successfully at: {xml_file_path}")
        
        # Generate validation reports
        validator.print_summary()
        
        # Save detailed validation reports
        reports_dir = args.report_dir
        
        # Save CSV report
        csv_report = validator.save_issues_to_csv(reports_dir)
        if csv_report:
            logger.info(f"Validation issues CSV report saved to: {csv_report}")
        
        # Generate HTML report
        html_report = validator.generate_html_report(reports_dir)
        logger.info(f"Validation HTML report saved to: {html_report}")
        
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()  
