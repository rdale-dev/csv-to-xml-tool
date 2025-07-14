# SBA Counseling and Training Data Conversion Tool

This utility is designed to process, clean, validate, and convert SBA (Small Business Administration) counseling and training data from CSV format into compliant XML files. It ensures the final XML adheres to the strict sequence and data requirements of the SBA NEXUS schemas for **Form 641 (Counseling)** and **Management Training Reports**.

The tool includes robust data cleaning, validation reporting, and a fixer utility for pre-existing XML files.

-----

## Key Features

  - **Dual Converters**:
      - [cite\_start]**Counseling Data (Form 641)**: Converts detailed client counseling session data into the `SBA_EDMIS_Counseling.xsd` format. [cite: 2, 8]
      - [cite\_start]**Training Data**: Aggregates participant data from training events and converts it into the `SBA_NEXUS_Training.xsd` format. [cite: 3]
  - **Data Cleaning & Standardization**:
      - [cite\_start]Formats dates to the required `YYYY-MM-DD` standard. [cite: 4]
      - [cite\_start]Cleans and validates phone numbers, numeric values, and percentages. [cite: 4]
      - [cite\_start]Standardizes state and country names to match schema enumerations (e.g., "IA" becomes "Iowa"). [cite: 4]
      - [cite\_start]Truncates long text fields, like counselor notes, to meet maximum length requirements while preserving readability. [cite: 4]
      - [cite\_start]Correctly handles and splits multi-value fields from Salesforce (e.g., `Race` or `Services Provided`). [cite: 4]
  - **XSD-Compliant XML Generation**:
      - [cite\_start]Generates XML with elements in the precise order required by the schemas, preventing common `cvc-complex-type.2.4.a` validation errors. [cite: 2]
      - [cite\_start]Correctly maps CSV data to the appropriate XML tags based on an extensive mapping configuration. [cite: 6]
      - [cite\_start]Handles conditional logic, such as requiring a `BranchOfService` only when `MilitaryStatus` indicates service. [cite: 2]
  - **Validation & Reporting**:
      - [cite\_start]Before conversion, the tool can analyze a CSV file to identify potential issues like missing required fields or invalid data formats. [cite: 8]
      - [cite\_start]During conversion, it generates comprehensive validation reports in both CSV and HTML formats, detailing any issues found in the source data. [cite: 8]
  - **XML Fixer Utility**:
      - [cite\_start]Includes a standalone script (`fix-sba-xml.py`) to correct element ordering issues in existing XML files that do not conform to the schema. [cite: 9]

-----

## Project Structure

```
.
├── main.py                     # Main entry point to run the converters and tests.
├── csv_to_xml.py               # Core logic for converting counseling data (Form 641).
├── classDataConverter.py       # Core logic for converting training class data.
├── data_cleaning.py            # Functions for cleaning, formatting, and standardizing data.
├── data_validation.py          # Functions for validating data integrity.
├── xml_utils.py                # Helper functions for creating XML elements.
├── config.py                   # Central configuration for field mappings, defaults, and validation rules.
├── validation_report.py        # Module for tracking and reporting validation issues.
├── logging_util.py             # Configures application-wide logging.
├── fix-sba-xml.py              # Utility to fix element order in existing SBA XML files.
└── SBA_EDMIS_Counseling.xsd    # The XML Schema Definition that defines the rules for counseling data.
```

-----

## How to Use

The primary entry point for the conversion is `main.py`.

### Prerequisites

  - Python 3.x
  - Pandas library (`pip install pandas`)

### Converting Counseling Data (Form 641)

This is the main conversion process for detailed client session reports.

1.  **Prepare your CSV file**. Ensure it contains the necessary columns as defined in `config.py`. [cite\_start]Your provided `report1748376042577.csv` is a good example. [cite: 6, 1]

2.  **Run the main script** from your terminal, providing the input and output paths.

    ```bash
    python main.py --input /path/to/your/report.csv --output /path/to/output/counseling_data.xml
    ```

### Converting Training Data

This process is for converting data related to training events and their attendees.

1.  **Prepare your training CSV file**. [cite\_start]This file should be structured with one row per participant per event, and must include a `Class/Event ID` to group attendees into the correct training event. [cite: 3]

2.  **Use the training data converter**. *Note: The `main.py` script may need to be adapted to select which converter to run. The following example assumes `classDataConverter.py` is run directly.*

    ```bash
    python classDataConverter.py /path/to/your/training_report.csv /path/to/output/training_data.xml
    ```

### Analyzing a CSV without Converting

To check a CSV file for potential issues before running the full conversion:

```bash
python main.py --input /path/to/your/report.csv --analyze-only
```

### Fixing an Existing XML File

[cite\_start]If you have an XML file that fails validation due to incorrect element order, use the `fix-sba-xml.py` script: [cite: 9]

```bash
python fix-sba-xml.py --file /path/to/your/invalid.xml --output /path/to/output/fixed.xml
```

[cite\_start]This will re-order the elements within the `<ClientIntake>` section to match the schema requirements. [cite: 9]

### Command-Line Arguments (`main.py`)

  - [cite\_start]`--input, -i`: Path to the input CSV file. [cite: 8]
  - `--output, -o`: (Optional) Path for the output XML file. [cite\_start]If omitted, the XML will be saved in the same directory as the input file with a timestamp. [cite: 8]
  - `--log-level`: Set the logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). [cite\_start]Defaults to `INFO`. [cite: 8]
  - `--report-dir`: Directory to save validation reports. [cite\_start]Defaults to `reports/`. [cite: 8]
  - `--log-dir`: Directory to save log files. [cite\_start]Defaults to `logs/`. [cite: 8]
  - [cite\_start]`--analyze-only`: Run a pre-validation analysis on the CSV without creating an XML file. [cite: 8]