# LLM Context Generator (`llmcontext`)

`llmcontext` is a Python command-line tool that recursively scans a specified directory, aggregates the content of its files, and formats this content for easy input into Large Language Models (LLMs). It intelligently ignores files and directories based on rules found in `.gitignore` and `.llmignore` files within the project structure.

This tool is useful for creating a comprehensive snapshot of a codebase or project that can then be fed to an LLM for analysis, summarization, code understanding, or other AI-driven tasks.

## Features

-   **Recursive Directory Scanning:** Traverses all subdirectories of the target directory.
-   **Content Aggregation:** Reads the content of discovered files.
-   **LLM-Friendly Formatting:** Outputs content with clear delimiters (`--filepath--`) for each file.
-   **Ignore File Handling:**
    -   Respects `.gitignore` files for standard project exclusion rules.
    -   Respects `.llmignore` files for LLM-specific exclusion rules (uses the same syntax as `.gitignore`).
    -   Patterns in deeper directories take precedence.
    -   Later patterns in the same file take precedence.
-   **UTF-8 Support:** Attempts to read files as UTF-8; skips binary or incompatible files with a notice.
-   **Customizable Input/Output:** Specify target directory and output file, with sensible defaults.
-   **Verbose Mode:** Optional verbose output for debugging and understanding which files are being processed or ignored.

## Prerequisites

-   **Python 3.6+**
-   **pip** (Python package installer)

## Installation

### Global Installation (Recommended)

Install `llmcontext` globally using pip or uv:

**Using pip:**
```bash
pip install llmcontext
```

**Using uv (faster):**
```bash
uv tool install llmcontext
```

### Local Development Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/llmcontext.git
    cd llmcontext
    ```

2.  **Install in development mode:**
    ```bash
    # Using pip
    pip install -e .
    
    # Using uv
    uv pip install -e .
    ```

### Manual Installation (Alternative)

If you prefer to install manually:

1.  **Download the source code and install dependencies:**
    ```bash
    pip install pathspec
    ```

2.  **Make the script executable:**
    ```bash
    chmod +x llmcontext.py
    ```

3.  **Add to PATH for global access:**
    ```bash
    # Move to a directory in your PATH
    sudo mv llmcontext.py /usr/local/bin/llmcontext
    ```

## Usage

Once installed and executable (and optionally in your PATH), you can run the script from your terminal.

**Basic Syntax:**

```bash
llmcontext [DIRECTORIES...] [-o OUTPUT_FILE] [--verbose]
```

**Arguments:**

-   `DIRECTORIES` (optional):
    -   One or more directories you want to scan (e.g., `dir1 dir2 dir3`).
    -   If not provided, defaults to the **current working directory** (`.`).
-   `-o, --output OUTPUT_FILE` (optional):
    -   The name of the file where the aggregated content will be saved.
    -   If not provided, defaults to `llmcontext.txt` in the **current working directory**.
-   `--verbose` or `-v` (optional):
    -   Enables verbose mode, which prints information about ignored files/directories, loaded patterns, and other diagnostics.

**Examples:**

1.  **Scan the current directory and output to `llmcontext.txt`:**
    ```bash
    llmcontext
    ```

2.  **Scan a specific project directory:**
    ```bash
    llmcontext /path/to/your/project
    ```

3.  **Scan multiple directories:**
    ```bash
    llmcontext /path/to/project1 /path/to/project2 /path/to/project3
    ```

4.  **Scan with custom output file:**
    ```bash
    llmcontext /path/to/your/project -o my_project_dump.txt
    # or using the long form:
    llmcontext /path/to/your/project --output my_project_dump.txt
    ```

5.  **Scan multiple directories with custom output:**
    ```bash
    llmcontext dir1 dir2 dir3 -o combined_output.txt
    ```

6.  **Scan with verbose output:**
    ```bash
    llmcontext --verbose /path/to/your/project
    # or combine with other options:
    llmcontext dir1 dir2 -o output.txt --verbose
    ```

## How `.llmignore` Works

The `.llmignore` file uses the same syntax as `.gitignore`. You can create `.llmignore` files in your project to specify files or directories that should be excluded *specifically* for the LLM context generation, even if they are tracked by Git.

**Example `.llmignore`:**

```
# Exclude all test data for LLM context
test_data/

# Exclude large model files not relevant for code understanding
*.pth
*.onnx

# Exclude specific documentation sections
docs/internal_only/
```

The script will process both `.gitignore` and `.llmignore` files found throughout the directory structure. Rules are combined, with patterns from files in deeper subdirectories (and patterns lower down in the same file) taking precedence.

## Output Format

The output file will contain the content of each processed file, prefixed by a header indicating its relative path:

```
--path/to/file1.py--
# Content of file1.py
...

--path/to/another/file2.js--
// Content of file2.js
...

--path/to/subdir/notes.txt--
Content of notes.txt
...
[Skipped: Binary or non-UTF-8 file]
...
```

## Creating a Standalone Executable (Optional)

If you want to run `llmcontext` on systems without Python or the `pathspec` library pre-installed, you can package it into a standalone executable using a tool like **PyInstaller**.

1.  **Install PyInstaller:**
    If you don't have PyInstaller installed, open your terminal and run:
    ```bash
    pip3 install pyinstaller
    ```

2.  **Navigate to the Script's Directory:**
    Open your terminal and change to the directory where `llmcontext.py` is located.

3.  **Build the Executable:**
    Run the following command:
    ```bash
    pyinstaller --onefile --name llmcontext llmcontext.py
    ```
    -   `--onefile`: This tells PyInstaller to bundle everything into a single executable file.
    -   `--name llmcontext`: This sets the name of the output executable to `llmcontext` (or `llmcontext.exe` on Windows).

4.  **Find the Executable:**
    PyInstaller will create a few folders (`build`, `dist`) and a `.spec` file. Your standalone executable will be located in the `dist` folder (e.g., `dist/llmcontext`).

5.  **Run the Executable:**
    You can now copy this single executable file (e.g., `dist/llmcontext`) to another machine (with the same OS and architecture) and run it directly:
    ```bash
    ./llmcontext /path/to/your/project output.txt
    ```

**Important Notes for Standalone Executables:**

-   **Platform Specific:** The executable created by PyInstaller is platform-specific. If you build it on macOS, it will run on macOS. If you need it for Windows, you'll need to run PyInstaller on a Windows machine (or use cross-compilation techniques, which can be more complex).
-   **File Size:** Single-file executables created by PyInstaller can be larger because they bundle parts of the Python interpreter and necessary libraries.
-   **Permissions:** Ensure the bundled executable has the necessary permissions to read files and directories in the target locations, especially if you move it to system directories or run it in restricted environments.
-   **Antivirus Software:** Occasionally, antivirus software might flag executables created by PyInstaller as suspicious (false positives) due to the way they unpack themselves at runtime. This is usually not an issue with well-known tools like PyInstaller when used with standard, non-malicious scripts.

## Contributing

Contributions are welcome! If you have suggestions for improvements or find any bugs, please feel free to open an issue or submit a pull request on the GitHub repository.

## License

This project is open-source and available under the [MIT License].
