"""
Logging utility for CSV to XML conversion.
This module provides configurable logging functionality for the conversion process.
"""

import logging
import os
from datetime import datetime

class ConversionLogger:
    """Handles logging for the CSV to XML conversion process."""
    
    def __init__(self, log_level=logging.INFO, log_to_file=True, log_dir="logs"):
        """
        Initialize the logger.
        
        Args:
            log_level: The logging level (default: INFO)
            log_to_file: Whether to save logs to a file (default: True)
            log_dir: Directory to store log files (default: "logs")
        """
        self.logger = logging.getLogger("csv_to_xml")
        self.logger.setLevel(log_level)
        self.logger.handlers = []  # Clear existing handlers to avoid duplicates
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Add file handler if enabled
        if log_to_file:
            # Create log directory if it doesn't exist
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            # Create log file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"conversion_{timestamp}.log")
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            self.logger.info(f"Log file created at: {log_file}")
    
    def info(self, message):
        """Log an info message."""
        self.logger.info(message)
    
    def warning(self, message, record_id=None):
        """
        Log a warning message.
        
        Args:
            message: The warning message
            record_id: Optional ID to identify the record with the issue
        """
        if record_id:
            self.logger.warning(f"[Record {record_id}] {message}")
        else:
            self.logger.warning(message)
    
    def error(self, message, record_id=None):
        """
        Log an error message.
        
        Args:
            message: The error message
            record_id: Optional ID to identify the record with the issue
        """
        if record_id:
            self.logger.error(f"[Record {record_id}] {message}")
        else:
            self.logger.error(message)
    
    def debug(self, message):
        """Log a debug message."""
        self.logger.debug(message)

# Create a default logger instance
logger = ConversionLogger()  
