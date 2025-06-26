#!/usr/bin/env python3
"""
Example usage and demonstrations of the e2e test suite
This file shows how to use the testing framework
"""

import sys
from pathlib import Path
import tempfile
import shutil

# Add the test directory to path
sys.path.insert(0, str(Path(__file__).parent))
from test_runner import LLMContextE2ETest


def example_basic_test():
    """Example of how to create a basic test"""
    
    class ExampleTest(LLMContextE2ETest):
        def test_basic_functionality(self):
            """Example test method"""
            input_dir = self.scenarios_dir / "simple_project"
            output_file = self.temp_dir / "example_output.txt"
            
            # Run llmcontext
            return_code, stdout, stderr = self.run_llmcontext(input_dir, output_file)
            
            # Check results
            self.assertEqual(return_code, 0)
            self.assertTrue(output_file.exists())
            
            # Check output content
            output_content = self.read_output_file(output_file)
            self.assert_file_in_output(output_content, "main.py")
            
    return ExampleTest


def example_custom_scenario():
    """Example of how to create and test a custom scenario"""
    
    # Create a temporary test scenario
    temp_scenario = Path(tempfile.mkdtemp())
    
    try:
        # Create test files
        (temp_scenario / "test.py").write_text("print('Hello from test scenario')")
        (temp_scenario / ".gitignore").write_text("*.log\ntemp/")
        (temp_scenario / "keep.txt").write_text("This should be included")
        (temp_scenario / "ignore.log").write_text("This should be ignored")
        
        # Create temp directory that should be ignored
        temp_dir = temp_scenario / "temp"
        temp_dir.mkdir()
        (temp_dir / "ignored_file.txt").write_text("This should be ignored")
        
        # Test the scenario
        test_instance = LLMContextE2ETest()
        test_instance.setUp()
        
        output_file = test_instance.temp_dir / "custom_output.txt"
        return_code, stdout, stderr = test_instance.run_llmcontext(temp_scenario, output_file)
        
        if return_code == 0:
            output_content = test_instance.read_output_file(output_file)
            print("Custom scenario test passed!")
            print(f"Output contains {len(output_content.split('--'))} files")
            
            # Verify expected files are included
            assert "--test.py--" in output_content
            assert "--keep.txt--" in output_content
            assert "--ignore.log--" not in output_content
            assert "--temp/ignored_file.txt--" not in output_content
            
            print("All assertions passed!")
        else:
            print(f"Test failed with return code {return_code}")
            print(f"Error: {stderr}")
            
        test_instance.tearDown()
        
    finally:
        # Clean up
        shutil.rmtree(temp_scenario)


def demonstrate_test_utilities():
    """Demonstrate the utility functions available in the test framework"""
    
    print("Test Framework Utilities:")
    print("=" * 30)
    
    print("1. LLMContextE2ETest.run_llmcontext(input_dir, output_file, verbose=False)")
    print("   - Runs the llmcontext tool and returns (return_code, stdout, stderr)")
    
    print("\n2. LLMContextE2ETest.read_output_file(output_file)")
    print("   - Reads and returns the content of an output file")
    
    print("\n3. LLMContextE2ETest.assert_file_in_output(output_content, filename)")
    print("   - Asserts that a file is present in the output")
    
    print("\n4. LLMContextE2ETest.assert_file_not_in_output(output_content, filename)")
    print("   - Asserts that a file is NOT present in the output")
    
    print("\n5. LLMContextE2ETest.assert_content_in_output(output_content, content)")
    print("   - Asserts that specific content is present in the output")
    
    print("\nAvailable test scenarios:")
    scenarios_dir = Path(__file__).parent / "test_scenarios"
    for scenario in scenarios_dir.iterdir():
        if scenario.is_dir():
            print(f"   - {scenario.name}")


def main():
    """Main function to run examples"""
    print("LLMContext E2E Test Examples")
    print("=" * 40)
    
    print("\n1. Running basic test example...")
    try:
        example_basic_test()
        print("✓ Basic test example completed")
    except Exception as e:
        print(f"✗ Basic test example failed: {e}")
    
    print("\n2. Running custom scenario example...")
    try:
        example_custom_scenario()
        print("✓ Custom scenario example completed")
    except Exception as e:
        print(f"✗ Custom scenario example failed: {e}")
    
    print("\n3. Demonstrating test utilities...")
    demonstrate_test_utilities()
    
    print("\n" + "=" * 40)
    print("Examples completed!")
    print("To run the full test suite, execute: python test_runner.py")


if __name__ == "__main__":
    main()