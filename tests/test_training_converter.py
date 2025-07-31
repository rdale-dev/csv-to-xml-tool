import unittest
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.converters.training_converter import TrainingConverter
from src.logging_util import ConversionLogger
from src.validation_report import ValidationTracker

class TestTrainingConverter(unittest.TestCase):

    def setUp(self):
        self.logger = ConversionLogger("test_training", log_level="DEBUG", log_to_file=False).logger
        self.validator = ValidationTracker()

    def test_converter_instantiation(self):
        """
        Tests that the TrainingConverter can be instantiated.
        """
        try:
            converter = TrainingConverter(self.logger, self.validator)
            self.assertIsInstance(converter, TrainingConverter)
        except Exception as e:
            self.fail(f"TrainingConverter instantiation failed with an exception: {e}")

if __name__ == '__main__':
    unittest.main()
