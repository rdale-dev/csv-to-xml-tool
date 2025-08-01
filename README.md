# SBA Counseling and Training Data Conversion Tool

This utility is designed to process, clean, validate, and convert SBA (Small Business Administration) counseling and training data from CSV format into compliant XML files. It ensures the final XML adheres to the strict sequence and data requirements of the SBA NEXUS schemas for **Form 641 (Counseling)** and **Management Training Reports**.

The tool includes robust data cleaning, validation reporting, and a fixer utility for pre-existing XML files.

-----

## Key Features

  * **Dual Converters**:
      * **Counseling Data (Form 641)**: Converts detailed client counseling session data.
      * **Training Data**: Aggregates participant data from training events and converts it.
  * **Data Cleaning & Standardization**:
      * Formats dates to the required `YYYY-MM-DD` standard.
      * Cleans and validates phone numbers, numeric values, and percentages.
      * Standardizes state and country names to match schema enumerations (e.g., "IA" becomes "Iowa").
      * Truncates long text fields, like counselor notes, to meet maximum length requirements while preserving readability.
      * Correctly handles and splits multi-value fields from Salesforce (e.g., `Race` or `Services Provided`).
  * **XSD-Compliant XML Generation**:
      * Generates XML with elements in the precise order required by the schemas, preventing common `cvc-complex-type.2.4.a` validation errors.
      * Correctly maps CSV data to the appropriate XML tags based on an extensive mapping configuration.
      * Handles conditional logic, such as requiring a `BranchOfService` only when `MilitaryStatus` indicates service.
  * **Validation & Reporting**:
      * During conversion, it generates comprehensive validation reports in both CSV and HTML formats, detailing any issues found in the source data.
  * **XML Fixer Utility**:
      * Includes a standalone script (`fix-sba-xml.py`) to correct element ordering issues in existing XML files that do not conform to the schema.

-----

## Project Structure

```
.
├── src/
│   ├── converters/
│   │   ├── base_converter.py       # Base class for all converters
│   │   ├── counseling_converter.py # Logic for converting counseling data (Form 641)
│   │   └── training_converter.py   # Logic for converting training class data
│   ├── main.py                     # Main entry point to run the converters
│   ├── data_cleaning.py            # Functions for cleaning, formatting, and standardizing data
│   ├── data_validation.py          # Functions for validating data integrity
│   ├── xml_utils.py                # Helper functions for creating XML elements
│   ├── config.py                   # Central configuration for field mappings, defaults, and validation rules
│   ├── validation_report.py        # Module for tracking and reporting validation issues
│   ├── logging_util.py             # Configures application-wide logging
│   ├── fix-sba-xml.py              # Utility to fix element order in existing SBA XML files
│   └── xml-validator.py            # Utility to validate XML files against an XSD
├── tests/
│   ├── test_counseling_converter.py
│   ├── test_data_cleaning.py
│   ├── test_training_converter.py
│   └── test_xml_utils.py
└── README.md
```

-----

## How to Use

The primary entry point for the conversion is `src/main.py`.

### Prerequisites

  * Python 3.x
  * Pandas library (`pip install pandas`)

### Converting Data

1.  **Prepare your CSV file**. Ensure it contains the necessary columns as defined in `src/config.py`.

2.  **Run the `main.py` script** from your terminal, specifying the `converter_type`, and providing the input and output paths.

    **For Counseling Data (Form 641):**

    ```bash
    python -m src.main convert counseling --input /path/to/your/report.csv --output /path/to/output/counseling_data.xml
    ```

    **For Training Data:**

    ```bash
    python -m src.main convert training --input /path/to/your/training_report.csv --output /path/to/output/training_data.xml
    ```

### Fixing an Existing XML File

If you have an XML file that fails validation due to incorrect element order, use the `fix-sba-xml.py` script:

```bash
python -m src.fix-sba-xml --file /path/to/your/invalid.xml --output /path/to/output/fixed.xml
```

This will re-order the elements to match the schema requirements.

### Command-Line Arguments (`main.py`)

  * `converter_type`: The type of conversion to perform (`counseling` or `training`).
  * `--input, -i`: Path to the input CSV file.
  * `--output, -o`: (Optional) Path for the output XML file. If omitted, the XML will be saved in the same directory as the input file with a timestamp.
  * `--log-level`: Set the logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). Defaults to `INFO`.
  * `--report-dir`: Directory to save validation reports. Defaults to `reports/`.
  * `--log-dir`: Directory to save log files. Defaults to `logs/`.
