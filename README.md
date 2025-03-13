# CSV to XML Conversion Tool

A tool for converting Salesforce counseling data from CSV format to XML according to a specific XSD schema.

## Project Structure

The application is organized into several modules with clear separation of concerns:

```
.
├── main.py                # Main entry point and CLI
├── csv_to_xml.py          # XML generation logic
├── data_cleaning.py       # Data transformation utilities
├── data_validation.py     # Data validation logic
├── config.py              # Configuration constants
├── logging_util.py        # Logging functionality
├── validation_report.py   # Validation tracking and reporting
├── logs/                  # Directory for log files
└── reports/               # Directory for validation reports
```

## Key Components

### 1. Main Module (`main.py`)
- Entry point for the application
- Command-line interface
- Orchestrates the conversion process

### 2. Configuration (`config.py`)
- Constants and configuration settings
- Field mappings between Salesforce and XML
- Validation categories
- Default values

### 3. Data Cleaning (`data_cleaning.py`)
- Pure data transformation functions
- Data format standardization
- No validation logic

### 4. Data Validation (`data_validation.py`)
- Validate data before conversion
- Track validation issues
- Analyze CSV data

### 5. CSV to XML Converter (`csv_to_xml.py`)
- Core XML generation logic
- Broken into modular functions
- Focuses solely on XML creation

### 6. Logging Utility (`logging_util.py`)
- Configurable logging functionality
- Console and file logging

### 7. Validation Reporting (`validation_report.py`)
- Tracks validation issues
- Generates validation reports (console, CSV, HTML)

## Features

- **Data Cleaning**
  - Country code standardization
  - Phone number formatting
  - Date formatting
  - Gender to sex mapping
  - Numeric and percentage cleaning
  - Text truncation for fields with length limits

- **Data Validation**
  - Required field validation
  - Format validation (dates, phone numbers, etc.)
  - Value validation (within allowed ranges)
  - Schema compliance checking

- **Reporting**
  - CSV analysis reports
  - Validation issue reports
  - HTML formatted reports
  - Console summaries

- **XML Generation**
  - Compliant with XSD schema
  - Proper nesting of elements
  - Default values for missing fields

## Usage

### Basic Usage

```bash
python main.py --input your_data.csv
```

### Command Line Arguments

| Argument | Short | Description |
|----------|-------|-------------|
| `--input` | `-i` | Path to the input CSV file |
| `--output` | `-o` | Path to the output XML file (optional) |
| `--log-level` | | Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO) |
| `--report-dir` | | Directory to save validation reports (default: reports) |
| `--log-dir` | | Directory to save log files (default: logs) |
| `--test-countries` | | Run country standardization test |
| `--analyze-only` | | Only analyze the CSV file without conversion |

### Examples

Basic conversion:
```bash
python main.py --input data/counseling_data.csv
```

Analyze CSV without conversion:
```bash
python main.py --input data/counseling_data.csv --analyze-only
```

Detailed debugging:
```bash
python main.py --input data/counseling_data.csv --log-level DEBUG
```

Test country standardization:
```bash
python main.py --test-countries
```

## Validation Reports

The tool generates multiple types of validation reports:

1. **Console Summary**: Overview of validation results
2. **CSV Report**: Detailed list of all validation issues
3. **HTML Report**: Formatted report with statistics and details

## Development Guide

### Adding New Validation Rules

1. Define constants in `config.py`
2. Add validation logic in `data_validation.py`
3. Register validation issue using `validator.add_issue()`

### Adding New XML Elements

1. Update field mappings in `config.py` if needed
2. Modify or add builder functions in `csv_to_xml.py`

### Adding New Data Cleaning Functions

1. Implement the function in `data_cleaning.py`
2. Keep functions pure (no side effects)
3. Add appropriate error handling

## Error Handling

The application uses several layers of error handling:

1. **Input validation**: Validates CSV data before processing
2. **Error logging**: Records errors with context
3. **Exception handling**: Catches and logs exceptions
4. **Non-blocking validation**: Reports issues but continues processing where possible
5. **Detailed reporting**: Provides comprehensive reports of all issues  
