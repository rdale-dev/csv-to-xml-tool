import unittest
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.converters.counseling_converter import CounselingConverter
from src.logging_util import ConversionLogger
from src.validation_report import ValidationTracker

class TestCounselingConverter(unittest.TestCase):

    def setUp(self):
        self.logger = ConversionLogger("test_counseling", log_level="DEBUG", log_to_file=False).logger
        self.validator = ValidationTracker()

    def test_converter_instantiation(self):
        """
        Tests that the CounselingConverter can be instantiated.
        """
        try:
            converter = CounselingConverter(self.logger, self.validator)
            self.assertIsInstance(converter, CounselingConverter)
        except Exception as e:
            self.fail(f"CounselingConverter instantiation failed with an exception: {e}")

if __name__ == '__main__':
    unittest.main()
