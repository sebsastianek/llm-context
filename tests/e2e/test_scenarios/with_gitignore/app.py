"""
Application with gitignore patterns for testing
"""

import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.data = []
        
    def load_data(self, filename):
        """Load data from file"""
        try:
            with open(filename, 'r') as f:
                self.data = [line.strip() for line in f.readlines()]
                logger.info(f"Loaded {len(self.data)} lines from {filename}")
        except FileNotFoundError:
            logger.error(f"File {filename} not found")
            
    def process_data(self):
        """Process loaded data"""
        processed = [line.upper() for line in self.data if line]
        logger.info(f"Processed {len(processed)} lines")
        return processed

if __name__ == "__main__":
    processor = DataProcessor()
    processor.load_data("input.txt")
    result = processor.process_data()
    print("Processed data:", result)