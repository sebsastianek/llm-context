#!/usr/bin/env python3
"""
End-to-end test runner for llmcontext tool
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import unittest
from typing import List, Dict, Any

# Add the parent directory to the path to import llmcontext
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import llmcontext


class LLMContextE2ETest(unittest.TestCase):
    """Base class for e2e tests"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(__file__).parent
        self.scenarios_dir = self.test_dir / "test_scenarios"
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def run_llmcontext(self, input_dirs, output_file: Path = None, verbose: bool = False) -> tuple:
        """
        Run llmcontext on one or more directories and return the result
        Returns (return_code, stdout, stderr)
        
        Args:
            input_dirs: Single Path or list of Paths to scan
            output_file: Output file path (optional)
            verbose: Enable verbose mode
        """
        if output_file is None:
            output_file = self.temp_dir / "output.txt"
        
        # Handle both single directory and multiple directories
        if isinstance(input_dirs, Path):
            input_dirs = [input_dirs]
        elif not isinstance(input_dirs, list):
            input_dirs = [input_dirs]
            
        cmd = [
            sys.executable, 
            str(Path(__file__).parent.parent.parent / "llmcontext.py")
        ]
        
        # Add directories
        for input_dir in input_dirs:
            cmd.append(str(input_dir))
        
        # Add output file option
        cmd.extend(["-o", str(output_file)])
        
        if verbose:
            cmd.append("--verbose")
            
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.temp_dir
        )
        
        return result.returncode, result.stdout, result.stderr
    
    def read_output_file(self, output_file: Path) -> str:
        """Read the contents of an output file"""
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def assert_file_in_output(self, output_content: str, filename: str):
        """Assert that a file is present in the output"""
        self.assertIn(f"--{filename}--", output_content, f"File {filename} not found in output")
    
    def assert_file_not_in_output(self, output_content: str, filename: str):
        """Assert that a file is NOT present in the output"""
        self.assertNotIn(f"--{filename}--", output_content, f"File {filename} should not be in output")
    
    def assert_content_in_output(self, output_content: str, content: str):
        """Assert that specific content is present in the output"""
        self.assertIn(content, output_content, f"Content '{content}' not found in output")


class TestSimpleProject(LLMContextE2ETest):
    """Test simple project without ignore patterns"""
    
    def test_simple_project_processing(self):
        """Test processing a simple project with basic files"""
        input_dir = self.scenarios_dir / "simple_project"
        output_file = self.temp_dir / "simple_output.txt"
        
        return_code, stdout, stderr = self.run_llmcontext(input_dir, output_file)
        
        self.assertEqual(return_code, 0, f"Command failed: {stderr}")
        self.assertTrue(output_file.exists(), "Output file was not created")
        
        output_content = self.read_output_file(output_file)
        
        # Check that all expected files are present
        self.assert_file_in_output(output_content, "main.py")
        self.assert_file_in_output(output_content, "utils.py")
        self.assert_file_in_output(output_content, "README.md")
        self.assert_file_in_output(output_content, "config.json")
        self.assert_file_in_output(output_content, "data/sample.txt")
        
        # Check that file contents are included
        self.assert_content_in_output(output_content, "def hello_world():")
        self.assert_content_in_output(output_content, "Simple Project")
        self.assert_content_in_output(output_content, '"app_name": "Simple Project"')


class TestGitignoreHandling(LLMContextE2ETest):
    """Test gitignore pattern handling"""
    
    def test_gitignore_patterns(self):
        """Test that gitignore patterns are respected"""
        input_dir = self.scenarios_dir / "with_gitignore"
        output_file = self.temp_dir / "gitignore_output.txt"
        
        return_code, stdout, stderr = self.run_llmcontext(input_dir, output_file, verbose=True)
        
        self.assertEqual(return_code, 0, f"Command failed: {stderr}")
        
        output_content = self.read_output_file(output_file)
        
        # Check that regular files are included
        self.assert_file_in_output(output_content, "app.py")
        self.assert_file_in_output(output_content, "input.txt")
        self.assert_file_in_output(output_content, ".gitignore")
        
        # Check that ignored files are NOT included
        self.assert_file_not_in_output(output_content, "should_be_ignored.log")
        self.assert_file_not_in_output(output_content, "temp/should_be_ignored.tmp")


class TestLLMIgnoreHandling(LLMContextE2ETest):
    """Test .llmignore pattern handling"""
    
    def test_llmignore_patterns(self):
        """Test that .llmignore patterns are respected"""
        input_dir = self.scenarios_dir / "with_llmignore"
        output_file = self.temp_dir / "llmignore_output.txt"
        
        return_code, stdout, stderr = self.run_llmcontext(input_dir, output_file, verbose=True)
        
        self.assertEqual(return_code, 0, f"Command failed: {stderr}")
        
        output_content = self.read_output_file(output_file)
        
        # Check that regular files are included
        self.assert_file_in_output(output_content, "main.py")
        self.assert_file_in_output(output_content, "public_readme.md")
        self.assert_file_in_output(output_content, ".llmignore")
        
        # Check that LLM-ignored files are NOT included
        self.assert_file_not_in_output(output_content, "large_data.csv")
        self.assert_file_not_in_output(output_content, "INTERNAL_NOTES.md")


class TestNestedStructure(LLMContextE2ETest):
    """Test nested directory structure with multiple .gitignore files"""
    
    def test_nested_gitignore_precedence(self):
        """Test that nested .gitignore files work with correct precedence"""
        input_dir = self.scenarios_dir / "nested_structure"
        output_file = self.temp_dir / "nested_output.txt"
        
        return_code, stdout, stderr = self.run_llmcontext(input_dir, output_file, verbose=True)
        
        self.assertEqual(return_code, 0, f"Command failed: {stderr}")
        
        output_content = self.read_output_file(output_file)
        
        # Check that source files are included
        self.assert_file_in_output(output_content, "src/core/engine.py")
        self.assert_file_in_output(output_content, "src/utils/helpers.py")
        self.assert_file_in_output(output_content, "src/api/handlers.py")
        self.assert_file_in_output(output_content, "tests/test_engine.py")
        
        # Check that content is properly included
        self.assert_content_in_output(output_content, "class Engine:")
        self.assert_content_in_output(output_content, "def load_json_config")


class TestBinaryFileHandling(LLMContextE2ETest):
    """Test handling of binary files"""
    
    def test_binary_file_skipping(self):
        """Test that binary files are properly skipped"""
        input_dir = self.scenarios_dir / "binary_files"
        output_file = self.temp_dir / "binary_output.txt"
        
        return_code, stdout, stderr = self.run_llmcontext(input_dir, output_file, verbose=True)
        
        self.assertEqual(return_code, 0, f"Command failed: {stderr}")
        
        output_content = self.read_output_file(output_file)
        
        # Check that text files are included
        self.assert_file_in_output(output_content, "text_file.txt")
        self.assert_file_in_output(output_content, "script.py")
        
        # Check that binary file is mentioned but content is skipped
        self.assert_file_in_output(output_content, "fake_image.png")
        self.assert_content_in_output(output_content, "[Skipped: Binary or non-UTF-8 file]")


class TestVerboseMode(LLMContextE2ETest):
    """Test verbose mode functionality"""
    
    def test_verbose_output(self):
        """Test that verbose mode provides additional information"""
        input_dir = self.scenarios_dir / "simple_project"
        output_file = self.temp_dir / "verbose_output.txt"
        
        return_code, stdout, stderr = self.run_llmcontext(input_dir, output_file, verbose=True)
        
        self.assertEqual(return_code, 0, f"Command failed: {stderr}")
        
        # Verbose mode should print information to stdout
        self.assertIn("Scanning directory:", stdout)
        self.assertIn("Successfully processed", stdout)


class TestMultipleDirectories(LLMContextE2ETest):
    """Test multiple directory functionality"""
    
    def test_multiple_directories_processing(self):
        """Test processing multiple directories"""
        input_dir1 = self.scenarios_dir / "simple_project"
        input_dir2 = self.scenarios_dir / "with_gitignore"
        output_file = self.temp_dir / "multi_output.txt"
        
        return_code, stdout, stderr = self.run_llmcontext([input_dir1, input_dir2], output_file)
        
        self.assertEqual(return_code, 0, f"Command failed: {stderr}")
        self.assertTrue(output_file.exists(), "Output file was not created")
        
        output_content = self.read_output_file(output_file)
        
        # Check that files from both directories are present
        # Files from simple_project
        self.assert_file_in_output(output_content, "main.py")
        self.assert_file_in_output(output_content, "utils.py")
        
        # Files from with_gitignore
        self.assert_file_in_output(output_content, "app.py")
        self.assert_file_in_output(output_content, "input.txt")
        
        # Check that directory headers are present for multiple directories
        self.assertIn("=== Directory:", output_content)
        self.assertIn("=== End of", output_content)
        
        # Check that both directory paths appear in headers
        self.assertIn(str(input_dir1), output_content)
        self.assertIn(str(input_dir2), output_content)
    
    def test_single_directory_no_headers(self):
        """Test that single directory processing doesn't include directory headers"""
        input_dir = self.scenarios_dir / "simple_project"
        output_file = self.temp_dir / "single_output.txt"
        
        return_code, stdout, stderr = self.run_llmcontext(input_dir, output_file)
        
        self.assertEqual(return_code, 0, f"Command failed: {stderr}")
        
        output_content = self.read_output_file(output_file)
        
        # Check that files are present
        self.assert_file_in_output(output_content, "main.py")
        
        # Check that directory headers are NOT present for single directory
        self.assertNotIn("=== Directory:", output_content)
        self.assertNotIn("=== End of", output_content)
    
    def test_output_flag_variants(self):
        """Test both -o and --output flag variants"""
        input_dir = self.scenarios_dir / "simple_project"
        
        # Test short form -o
        output_file1 = self.temp_dir / "short_flag_output.txt"
        return_code1, stdout1, stderr1 = self.run_llmcontext(input_dir, output_file1)
        self.assertEqual(return_code1, 0, f"Short flag test failed: {stderr1}")
        self.assertTrue(output_file1.exists())
        
        # Test that content is properly written
        output_content1 = self.read_output_file(output_file1)
        self.assert_file_in_output(output_content1, "main.py")
    
    def test_verbose_with_multiple_directories(self):
        """Test verbose mode with multiple directories"""
        input_dir1 = self.scenarios_dir / "simple_project"
        input_dir2 = self.scenarios_dir / "binary_files"
        output_file = self.temp_dir / "verbose_multi_output.txt"
        
        return_code, stdout, stderr = self.run_llmcontext([input_dir1, input_dir2], output_file, verbose=True)
        
        self.assertEqual(return_code, 0, f"Command failed: {stderr}")
        
        # Check verbose output mentions multiple directories
        self.assertIn("Scanning 2 directories:", stdout)
        self.assertIn("Successfully processed 2 directories", stdout)


class TestNewCLIInterface(LLMContextE2ETest):
    """Test the new CLI interface specifically"""
    
    def test_default_directory_behavior(self):
        """Test that default directory behavior works with new interface"""
        # Create a simple test structure in temp directory
        test_file = self.temp_dir / "test.txt"
        test_file.write_text("test content")
        
        output_file = self.temp_dir / "output.txt"
        
        # Run from the temp directory without specifying input directory
        cmd = [
            sys.executable,
            str(Path(__file__).parent.parent.parent / "llmcontext.py"),
            "-o", str(output_file)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.temp_dir
        )
        
        self.assertEqual(result.returncode, 0, f"Command failed: {result.stderr}")
        self.assertTrue(output_file.exists())
        
        output_content = self.read_output_file(output_file)
        self.assert_file_in_output(output_content, "test.txt")
        self.assert_content_in_output(output_content, "test content")


def run_all_tests():
    """Run all e2e tests and return results"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestSimpleProject,
        TestGitignoreHandling,
        TestLLMIgnoreHandling,
        TestNestedStructure,
        TestBinaryFileHandling,
        TestVerboseMode,
        TestMultipleDirectories,
        TestNewCLIInterface
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    print("Running LLMContext E2E Tests")
    print("=" * 50)
    
    result = run_all_tests()
    
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)