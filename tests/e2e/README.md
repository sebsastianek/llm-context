# LLMContext E2E Tests

This directory contains comprehensive end-to-end tests for the `llmcontext` tool.

## Structure

```
tests/e2e/
├── README.md                 # This file
├── test_runner.py           # Main test runner with all test cases
├── run_tests.py            # Simple script to run tests
├── test_examples.py        # Examples and demonstrations
└── test_scenarios/         # Test data scenarios
    ├── simple_project/     # Basic project without ignore patterns
    ├── with_gitignore/     # Project with .gitignore patterns
    ├── with_llmignore/     # Project with .llmignore patterns
    ├── nested_structure/   # Complex nested directory structure
    ├── binary_files/       # Mixed text and binary files
    └── edge_cases/         # Edge cases (unicode, long names, etc.)
```

## Test Scenarios

### 1. Simple Project (`simple_project/`)
- Basic Python files (`main.py`, `utils.py`)
- Configuration file (`config.json`)
- Documentation (`README.md`)
- Data directory with sample files
- **Tests**: Basic file processing and content inclusion

### 2. With Gitignore (`with_gitignore/`)
- Python application with logging
- `.gitignore` file with common patterns
- Files that should be ignored (`.log`, `temp/` directory)
- **Tests**: Gitignore pattern respect and file exclusion

### 3. With LLMIgnore (`with_llmignore/`)
- Project with LLM-specific ignore patterns
- `.llmignore` file excluding data files and internal docs
- Large data files (CSV) that should be ignored
- Internal documentation that should be excluded
- **Tests**: LLM-specific ignore patterns and precedence

### 4. Nested Structure (`nested_structure/`)
- Multi-level directory structure (`src/`, `tests/`)
- Multiple `.gitignore` files at different levels
- Python package structure with imports
- **Tests**: Nested ignore file precedence and complex directory traversal

### 5. Binary Files (`binary_files/`)
- Mix of text and binary files
- Fake PNG file (binary data)
- Regular text and Python files
- **Tests**: Binary file detection and skipping

### 6. Edge Cases (`edge_cases/`)
- Empty files
- Unicode content (emojis, international characters)
- Very long filenames
- Filenames with spaces and special characters
- **Tests**: Edge case handling and robustness

## Running Tests

### Run All Tests
```bash
python tests/e2e/test_runner.py
```

### Run Tests with Simple Script
```bash
python tests/e2e/run_tests.py
```

### Run Examples and Demonstrations
```bash
python tests/e2e/test_examples.py
```

## Test Classes

### `LLMContextE2ETest` (Base Class)
Base class providing common test utilities:

- `run_llmcontext(input_dir, output_file, verbose)` - Execute llmcontext tool
- `read_output_file(output_file)` - Read output file contents
- `assert_file_in_output(output_content, filename)` - Assert file presence
- `assert_file_not_in_output(output_content, filename)` - Assert file absence
- `assert_content_in_output(output_content, content)` - Assert content presence

### Test Classes
- `TestSimpleProject` - Basic functionality tests
- `TestGitignoreHandling` - Gitignore pattern tests
- `TestLLMIgnoreHandling` - LLMignore pattern tests
- `TestNestedStructure` - Complex directory structure tests
- `TestBinaryFileHandling` - Binary file handling tests
- `TestVerboseMode` - Verbose output tests

## Creating Custom Tests

### 1. Extend the Base Class
```python
class MyCustomTest(LLMContextE2ETest):
    def test_my_feature(self):
        input_dir = self.scenarios_dir / "my_scenario"
        output_file = self.temp_dir / "my_output.txt"
        
        return_code, stdout, stderr = self.run_llmcontext(input_dir, output_file)
        
        self.assertEqual(return_code, 0)
        output_content = self.read_output_file(output_file)
        self.assert_file_in_output(output_content, "expected_file.py")
```

### 2. Create Test Scenario Data
Create a new directory under `test_scenarios/` with your test files and ignore patterns.

### 3. Add to Test Runner
Add your test class to the `test_classes` list in `test_runner.py`.

## Test Coverage

The e2e tests cover:

✅ Basic file processing and output formatting  
✅ Gitignore pattern handling and file exclusion  
✅ LLMignore pattern handling and LLM-specific exclusions  
✅ Nested directory structures with multiple ignore files  
✅ Binary file detection and proper skipping  
✅ Unicode content handling  
✅ Edge cases (empty files, long names, special characters)  
✅ Verbose mode functionality  
✅ Error handling and graceful failure  

## Dependencies

The tests use Python's built-in `unittest` framework and don't require additional dependencies beyond what's needed for the main `llmcontext` tool.

## Continuous Integration

These tests can be easily integrated into CI/CD pipelines:

```bash
# In your CI script
cd /path/to/llmcontext
python tests/e2e/test_runner.py
```

The test runner exits with appropriate status codes for CI integration.