#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
import pathspec  # For .gitignore style matching


def load_ignore_patterns(root_dir: Path, verbose: bool = False) -> pathspec.PathSpec:
    """
    Loads all .gitignore and .llmignore patterns recursively from root_dir downwards.
    Patterns are made relative to root_dir.
    Patterns from deeper files or later in a file take precedence.
    """
    # Stores (pattern_line, source_ignore_file_dir)
    all_patterns_with_source_dir = []

    # Discover all .gitignore and .llmignore files within the root_dir
    # These are the only sources for ignore patterns.
    for ignore_filename in [".gitignore", ".llmignore"]:
        # Using rglob to find all relevant ignore files
        # The "**/" prefix ensures it searches in root_dir and all subdirectories.
        for ignore_file_path in root_dir.rglob(f"**/{ignore_filename}"):
            if ignore_file_path.is_file():  # Ensure it's a file, not a directory named .gitignore
                if verbose:
                    print(
                        f"Reading ignore file: {ignore_file_path.relative_to(root_dir.parent)}")  # Show path relative to project for clarity
                try:
                    with ignore_file_path.open('r', encoding='utf-8', errors='ignore') as f:
                        lines = f.read().splitlines()
                    ignore_file_parent_dir = ignore_file_path.parent
                    for line in lines:
                        stripped_line = line.strip()
                        # Ignore empty lines and comments
                        if stripped_line and not stripped_line.startswith("#"):
                            all_patterns_with_source_dir.append((stripped_line, ignore_file_parent_dir))
                except Exception as e:
                    if verbose:
                        print(f"  Warning: Could not read {ignore_file_path.relative_to(root_dir.parent)}: {e}")

    # Sort patterns:
    # Patterns from more specific (deeper) .gitignore files should come *later*
    # to override patterns from less specific (shallower) .gitignore files.
    # We sort by the depth of the directory containing the ignore file (shallower first).
    # When these are added to final_pat_list, those from deeper files (processed later in this sorted list)
    # will be added later to `final_pat_list`, thus having higher precedence in pathspec.
    all_patterns_with_source_dir.sort(
        key=lambda x: len(x[1].relative_to(root_dir).parts) if x[1].is_relative_to(root_dir) else float('inf')
    )

    final_pat_list = []
    for pattern_line, source_dir in all_patterns_with_source_dir:
        # Make the pattern relative to root_dir for pathspec matching
        # path_prefix is the path from root_dir to the directory containing the ignore file
        path_prefix = source_dir.relative_to(root_dir) if source_dir.is_relative_to(root_dir) else Path()

        if pattern_line.startswith('/'):
            # A leading slash means the pattern is relative to the directory containing the ignore file.
            # For pathspec, which matches relative to root_dir, we prepend the path_prefix.
            final_pattern = (path_prefix / pattern_line.lstrip('/')).as_posix()
        else:
            # No leading slash means the pattern can match at any level.
            # However, git matches relative to the ignore file's dir.
            # For pathspec, we need to make it relative to root_dir.
            # If the pattern is like `*.log` from `root/subdir/.gitignore`, it means `root/subdir/*.log`.
            # So, `path_prefix / pattern_line` is correct.
            final_pattern = (path_prefix / pattern_line).as_posix()

        # Normalize pattern (e.g. remove './', handle '..') and ensure forward slashes
        final_pattern = os.path.normpath(final_pattern).replace(os.sep, '/')
        if final_pattern == '.':  # Skip patterns that normalize to nothing (e.g. './')
            continue

        final_pat_list.append(final_pattern)
        if verbose:
            print(
                f"  Loaded pattern: '{pattern_line}' from {source_dir.relative_to(root_dir.parent)} -> effective as: '{final_pattern}'")

    if verbose and not final_pat_list:
        print("No custom ignore patterns found or loaded from .gitignore or .llmignore files.")
    if verbose and final_pat_list:
        print(f"Final list of patterns for PathSpec: {final_pat_list}")

    # 'gitwildmatch' is the style of patterns used in .gitignore files
    return pathspec.PathSpec.from_lines('gitwildmatch', final_pat_list)


def should_ignore(path_to_check: Path, root_directory: Path, spec: pathspec.PathSpec, verbose: bool = False) -> bool:
    """
    Check if a given path should be ignored based on the loaded PathSpec.
    path_to_check should be an absolute path.
    root_directory is the absolute path against which patterns were made relative.
    """
    try:
        # Ensure both paths are absolute for reliable relative_to comparison
        abs_path_to_check = path_to_check.resolve()
        abs_root_directory = root_directory.resolve()

        # The path given to pathspec must be relative to the root_directory
        relative_path = abs_path_to_check.relative_to(abs_root_directory)
    except ValueError:
        # This can happen if path_to_check is not under root_directory.
        # Such paths are outside the scope of the current scan based on root_directory.
        if verbose:
            print(f"  Path {abs_path_to_check} is outside scan root {abs_root_directory}, not checking for ignore.")
        return False

        # Convert the relative path to a string with POSIX-style forward slashes, as gitignore patterns expect
    path_str = str(relative_path.as_posix())

    # For directory matching, gitignore patterns often expect a trailing slash.
    # Pathspec handles this: if a pattern is "dir/", it matches "dir/" but not "dir".
    # If path_to_check is a directory, we append a slash to path_str for matching.
    if abs_path_to_check.is_dir():
        path_str += "/"

    is_ignored = spec.match_file(path_str)
    if verbose and is_ignored:
        print(
            f"  Path '{path_str}' (from {abs_path_to_check.relative_to(abs_root_directory.parent)}) matched ignore patterns.")
    return is_ignored


def process_directory_content(directory: Path, spec: pathspec.PathSpec, verbose: bool = False):
    """
    Recursively processes files in the directory using os.walk for better ignore handling.
    Returns content as a list of strings.
    """
    collected_content = []
    root_dir_abs = directory.resolve()  # Absolute path of the directory to scan

    # os.walk yields (dirpath, dirnames, filenames)
    # dirpath is a string, path to the current directory
    # dirnames is a list of names of subdirectories in dirpath
    # filenames is a list of names of non-directory files in dirpath
    for dirpath_str, dirnames, filenames in os.walk(str(root_dir_abs), topdown=True):
        current_dir_path_abs = Path(dirpath_str).resolve()

        # Filter out ignored directories from dirnames *in place* to prevent os.walk from descending
        original_dirnames = list(dirnames)  # Make a copy for iteration as we modify dirnames
        dirnames[:] = [
            d_name for d_name in original_dirnames
            if not should_ignore((current_dir_path_abs / d_name), root_dir_abs, spec, verbose=verbose)
        ]

        if verbose:
            ignored_dirs_in_step = set(original_dirnames) - set(dirnames)
            if ignored_dirs_in_step:
                for ignored_d in ignored_dirs_in_step:
                    # Show path relative to the initial scan directory for clarity
                    print(f"  Ignoring directory: {(current_dir_path_abs / ignored_d).relative_to(root_dir_abs)}")

        for filename in filenames:
            file_path_abs = (current_dir_path_abs / filename).resolve()

            # Check if the file itself should be ignored
            if should_ignore(file_path_abs, root_dir_abs, spec, verbose=verbose):
                # Verbose message for ignoring file already printed by should_ignore if verbose
                continue

            try:
                # Path for the output file header, relative to the initial scan directory
                relative_path_to_root = file_path_abs.relative_to(root_dir_abs).as_posix()
                try:
                    # Attempt to read as UTF-8. If it's binary or wrong encoding, skip with a message.
                    with file_path_abs.open('r', encoding='utf-8', errors='strict') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    content = "[Skipped: Binary or non-UTF-8 file]"
                    if verbose:
                        print(f"  Skipping binary/non-UTF-8 file: {relative_path_to_root}")
                except Exception as e:  # Catch other read errors (e.g., permission denied)
                    content = f"[Error reading file: {e}]"
                    if verbose:
                        print(f"  Error reading file {relative_path_to_root}: {e}")

                collected_content.append(f"--{relative_path_to_root}--\n{content}\n\n")
            except Exception as e:
                # This outer exception is for critical errors like path resolution issues
                if verbose:
                    print(f"Critical error processing file metadata for {file_path_abs}: {e}")
                try:
                    rel_path_on_error = file_path_abs.relative_to(root_dir_abs).as_posix()
                except:  # Fallback if relative path itself fails
                    rel_path_on_error = str(file_path_abs)
                collected_content.append(f"--{rel_path_on_error}--\n[Error processing file meta: {e}]\n\n")

    return collected_content


def process_directory(directory: Path, output_file: Path, spec: pathspec.PathSpec, verbose: bool = False):
    """
    Recursively processes files in the directory using os.walk for better ignore handling.
    Writes content to the output_file. (Legacy function for backward compatibility)
    """
    collected_content = process_directory_content(directory, spec, verbose)
    
    try:
        with output_file.open('w', encoding='utf-8') as f:
            f.writelines(collected_content)  # More efficient for list of strings
        print(f"Successfully processed directory. Output written to {output_file.resolve()}")
    except IOError as e:
        print(f"Error: Could not write to output file {output_file.resolve()}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Recursively scans one or more directories, reads file contents, and formats them for LLM analysis. "
                    "Obeys .gitignore and .llmignore rules. Output includes file paths as headers.",
        formatter_class=argparse.RawTextHelpFormatter  # Allows for better formatting of help text
    )
    parser.add_argument(
        "directories",
        type=str,
        nargs='*',  # Accept zero or more directories
        default=['.'],  # Default to current directory if not provided
        help="The target directories to scan (e.g., /path/to/project1 /path/to/project2).\n"
             "If not specified, defaults to the current working directory."
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default='llmcontext.txt',  # Default output filename
        help="The file to write the aggregated content to (e.g., project_context.txt).\n"
             "If not specified, defaults to 'llmcontext.txt' in the current working directory."
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output, showing ignored files/directories and other diagnostic information."
    )

    args = parser.parse_args()

    # Handle default case when no directories are provided
    if not args.directories:
        args.directories = ['.']

    # Resolve input directories to absolute paths for consistency
    input_dirs = []
    for directory in args.directories:
        input_dir = Path(directory).resolve()
        if not input_dir.is_dir():
            print(f"Error: Input directory '{directory}' (resolved to '{input_dir}') does not exist or is not a directory.")
            return
        input_dirs.append(input_dir)

    # Determine output file path. If not absolute, make it relative to current working directory.
    output_f = Path(args.output)
    if not output_f.is_absolute():
        output_f = Path.cwd() / output_f
    output_f = output_f.resolve()  # Ensure output path is absolute as well

    print(f"Starting LLM Context Generator...")
    if len(input_dirs) == 1:
        print(f"Scanning directory: {input_dirs[0]}")
    else:
        print(f"Scanning {len(input_dirs)} directories:")
        for input_dir in input_dirs:
            print(f"  - {input_dir}")

    # Warn if output file exists, as it will be overwritten.
    if output_f.exists():
        print(f"Warning: Output file '{output_f}' already exists. It will be overwritten.")

    print(f"Output will be saved to: {output_f}")
    if args.verbose:
        print("Verbose mode enabled.")

    # Process all directories and generate the output
    collected_content = []
    for input_dir in input_dirs:
        if args.verbose:
            print(f"\nProcessing directory: {input_dir}")
        
        # Load ignore patterns from .gitignore and .llmignore files for this directory
        ignore_spec = load_ignore_patterns(input_dir, verbose=args.verbose)
        
        # Process the directory and collect content
        dir_content = process_directory_content(input_dir, ignore_spec, verbose=args.verbose)
        if len(input_dirs) > 1:
            # Add a section header when processing multiple directories
            collected_content.append(f"=== Directory: {input_dir} ===\n\n")
        collected_content.extend(dir_content)
        if len(input_dirs) > 1:
            collected_content.append(f"\n=== End of {input_dir} ===\n\n")

    # Write all collected content to the output file
    try:
        with output_f.open('w', encoding='utf-8') as f:
            f.writelines(collected_content)
        print(f"Successfully processed {len(input_dirs)} director{'y' if len(input_dirs) == 1 else 'ies'}. Output written to {output_f.resolve()}")
    except IOError as e:
        print(f"Error: Could not write to output file {output_f.resolve()}: {e}")


if __name__ == "__main__":
    main()
