"""
Tests for the core engine
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.engine import Engine

class TestEngine(unittest.TestCase):
    def setUp(self):
        self.engine = Engine({'debug': True})
        
    def test_engine_start_stop(self):
        """Test engine start and stop"""
        self.assertFalse(self.engine.running)
        self.engine.start()
        self.assertTrue(self.engine.running)
        self.engine.stop()
        self.assertFalse(self.engine.running)
        
    def test_engine_process(self):
        """Test engine data processing"""
        self.engine.start()
        result = self.engine.process("test data")
        self.assertEqual(result, "Processed: test data")
        
    def test_engine_process_not_running(self):
        """Test engine processing when not running"""
        with self.assertRaises(RuntimeError):
            self.engine.process("test data")

if __name__ == '__main__':
    unittest.main()