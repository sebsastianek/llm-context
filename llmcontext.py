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
            # Example: /foo.txt from root/A/.gitignore -> A/foo.txt
            final_pattern = (path_prefix / pattern_line.lstrip('/')).as_posix()
        elif '/' in pattern_line:
            # Contains a slash, but doesn't start with one. Relative to the ignore file's directory.
            # Example: build/output from root/A/.gitignore -> A/build/output
            final_pattern = (path_prefix / pattern_line).as_posix()
        else:
            # No slashes at all (e.g., "*.log", "tempfile").
            # These patterns match in the current directory and subdirectories thereof.
            if not path_prefix.parts:  # Empty path_prefix means ignore file is in root_dir
                # Example: *.log from root/.gitignore -> *.log (matches globally)
                final_pattern = pattern_line
            else:  # Pattern from a subdirectory's ignore file, e.g. root/A/.gitignore wants to ignore *.log
                # This makes it match 'A/file.log' and 'A/subdir/file.log' etc.
                # The pattern needs to be anchored to the path of the ignore file's directory,
                # and then apply globbing within that scope.
                # Example: *.log from root/A/.gitignore -> A/**/*.log
                current_prefix_str = path_prefix.as_posix()
                if current_prefix_str == ".": # Path(".").as_posix() is "."
                    current_prefix_str = "" # Avoid "./**/*.log"

                if current_prefix_str:
                    final_pattern = f"{current_prefix_str}/**/{pattern_line}"
                else: # This case implies path_prefix was effectively root, though logic for that is above.
                      # This is a safeguard. If path_prefix.parts is true, current_prefix_str should not be empty unless it was ".".
                    final_pattern = f"**/{pattern_line}" # Effectively `**/{pattern_line}` if pathspec implies root, same as if from root .gitignore

        # General normalization and ensuring POSIX slashes
        # Pathlib's construction (`/`) and `as_posix()` already handle most slash normalization.
        # `os.path.normpath` can be tricky as it might use backslashes on Windows or alter `**`.
        # We primarily need to ensure forward slashes and handle trivial cases like './'.

        # Convert to string and ensure forward slashes, as PathSpec expects POSIX-style paths.
        # This was `final_pattern = os.path.normpath(final_pattern).replace(os.sep, '/')`
        # Let's simplify: Path objects internally manage normalization to some extent.
        # The construction above should result in POSIX paths due to .as_posix() and f-string.
        # If `final_pattern` is already a string (e.g. from `pattern_line` itself), ensure it's POSIX.
        final_pattern = str(final_pattern).replace(os.sep, '/')

        # Remove './' from the beginning of a pattern, if it exists, as it's mostly redundant for pathspec matching.
        # e.g. "./foo/bar" -> "foo/bar"
        if final_pattern.startswith('./'):
            final_pattern = final_pattern[2:]

        # Preserve trailing slash if original pattern had it (for directories) and it got lost
        if pattern_line.endswith('/') and not final_pattern.endswith('/') and final_pattern: # final_pattern can be empty if original was './'
            final_pattern += '/'

        # Skip patterns that normalize to nothing or just a slash (e.g. './' or '/')
        # A pattern like "/" from root usually means "ignore files/dirs in root only", not everything.
        # However, pathspec might interpret "/" as matching everything if not careful.
        # The original code had `if final_pattern == '.': continue`. Let's refine this.
        # An empty pattern or a pattern that is just "/" (unless intended for root contents) is problematic.
        if not final_pattern or final_pattern == '.':
            continue

        # If a pattern was originally just "/", from a nested ignore file like "A//",
        # it would become "A/" (correctly). From root, it would be "/".
        # Pathspec treats "/" as "match files and directories at the root".
        # This is usually fine.

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


def should_ignore(path_to_check: Path, spec_root_dir: Path, spec: pathspec.PathSpec, verbose: bool = False) -> bool:
    """
    Check if a given path should be ignored based on the loaded PathSpec.
    path_to_check should be an absolute path.
    spec_root_dir is the absolute path against which patterns in spec were made relative.
    """
    try:
        # Ensure both paths are absolute for reliable relative_to comparison
        abs_path_to_check = path_to_check.resolve()
        abs_spec_root_dir = spec_root_dir.resolve()

        # The path given to pathspec must be relative to the spec_root_dir
        relative_path = abs_path_to_check.relative_to(abs_spec_root_dir)
    except ValueError:
        # This can happen if path_to_check is not under spec_root_dir.
        # Such paths are outside the scope of the current ignore patterns.
        if verbose:
            print(f"  Path {abs_path_to_check} is outside spec root {abs_spec_root_dir}, not checking for ignore.")
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
        # Show path relative to the parent of the spec_root_dir for possibly cleaner verbose output
        # or relative to spec_root_dir itself.
        try:
            display_path_origin = abs_path_to_check.relative_to(abs_spec_root_dir.parent)
        except ValueError:
            display_path_origin = abs_path_to_check # fallback to absolute
        print(
            f"  Path '{path_str}' (from {display_path_origin}) matched ignore patterns relative to {abs_spec_root_dir}.")
    return is_ignored


def process_directory(
    content_scan_dir: Path,
    output_file: Path,
    spec: pathspec.PathSpec,
    spec_root_dir: Path,
    verbose: bool = False
):
    """
    Recursively processes files in content_scan_dir using os.walk.
    Ignore patterns in spec are relative to spec_root_dir.
    Writes content to output_file.
    """
    collected_content = []
    # content_scan_dir_abs is the root for os.walk and for making header paths relative for output
    content_scan_dir_abs = content_scan_dir.resolve()

    # os.walk yields (dirpath, dirnames, filenames)
    # dirpath is a string, path to the current directory
    # dirnames is a list of names of subdirectories in dirpath
    # filenames is a list of names of non-directory files in dirpath
    # os.walk starts from content_scan_dir_abs
    for dirpath_str, dirnames, filenames in os.walk(str(content_scan_dir_abs), topdown=True):
        current_dir_path_abs = Path(dirpath_str).resolve()

        # Filter out ignored directories from dirnames *in place* to prevent os.walk from descending
        # Paths are checked against spec, which is relative to spec_root_dir
        original_dirnames = list(dirnames)  # Make a copy for iteration as we modify dirnames
        dirnames[:] = [
            d_name for d_name in original_dirnames
            if not should_ignore((current_dir_path_abs / d_name), spec_root_dir, spec, verbose=verbose)
        ]

        if verbose:
            ignored_dirs_in_step = set(original_dirnames) - set(dirnames)
            if ignored_dirs_in_step:
                for ignored_d in ignored_dirs_in_step:
                    # Show path relative to the content_scan_dir_abs for clarity of what's being skipped in the walk
                    print(f"  Ignoring directory during walk: {(current_dir_path_abs / ignored_d).relative_to(content_scan_dir_abs)}")

        for filename in filenames:
            file_path_abs = (current_dir_path_abs / filename).resolve()

            # Check if the file itself should be ignored
            # Paths are checked against spec, which is relative to spec_root_dir
            if should_ignore(file_path_abs, spec_root_dir, spec, verbose=verbose):
                # Verbose message for ignoring file already printed by should_ignore if verbose
                continue

            try:
                # Path for the output file header, relative to content_scan_dir_abs
                relative_path_for_header = file_path_abs.relative_to(content_scan_dir_abs).as_posix()
                try:
                    # Attempt to read as UTF-8. If it's binary or wrong encoding, skip with a message.
                    with file_path_abs.open('r', encoding='utf-8', errors='strict') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    content = "[Skipped: Binary or non-UTF-8 file]"
                    if verbose:
                        print(f"  Skipping binary/non-UTF-8 file: {relative_path_for_header}")
                except Exception as e:  # Catch other read errors (e.g., permission denied)
                    content = f"[Error reading file: {e}]"
                    if verbose:
                        print(f"  Error reading file {relative_path_for_header}: {e}")

                collected_content.append(f"--{relative_path_for_header}--\n{content}\n\n")
            except Exception as e:
                # This outer exception is for critical errors like path resolution issues
                if verbose:
                    print(f"Critical error processing file metadata for {file_path_abs}: {e}")
                try:
                    # Fallback relative path for header in case of error
                    rel_path_on_error = file_path_abs.relative_to(content_scan_dir_abs).as_posix()
                except:  # Fallback if relative path itself fails
                    rel_path_on_error = str(file_path_abs)
                collected_content.append(f"--{rel_path_on_error}--\n[Error processing file meta: {e}]\n\n")

    try:
        with output_file.open('w', encoding='utf-8') as f:
            f.writelines(collected_content)  # More efficient for list of strings
        print(f"Successfully processed directory. Output written to {output_file.resolve()}")
    except IOError as e:
        print(f"Error: Could not write to output file {output_file.resolve()}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Recursively scans a directory, reads file contents, and formats them for LLM analysis. "
                    "Obeys .gitignore and .llmignore rules. Output includes file paths as headers.",
        formatter_class=argparse.RawTextHelpFormatter  # Allows for better formatting of help text
    )
    parser.add_argument(
        "directory",
        type=str,
        nargs='?',  # Makes the argument optional
        default='.',  # Default to current directory if not provided
        help="The target directory to scan (e.g., /path/to/project).\n"
             "If not specified, defaults to the current working directory."
    )
    parser.add_argument(
        "output_file",
        type=str,
        nargs='?',  # Makes the argument optional
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

    # Resolve input directory to an absolute path for consistency
    input_dir_abs = Path(args.directory).resolve()

    # Determine the root directory for scanning ignore files
    # This can be different from input_dir_abs, especially if args.directory is relative.
    scan_root_for_ignores: Path
    original_input_path = Path(args.directory)

    if original_input_path.is_absolute():
        scan_root_for_ignores = input_dir_abs
        if args.verbose:
            print(f"Input path is absolute. Ignore patterns will be loaded from: {scan_root_for_ignores} downwards.")
    else:
        cwd = Path.cwd()
        scan_root_for_ignores = find_project_root_for_ignores(cwd, verbose=args.verbose)
        if args.verbose:
            print(f"Input path is relative. Current directory: {cwd}")
            print(f"Effective project root for ignores: {scan_root_for_ignores}")
            print(f"Actual content scan will be within: {input_dir_abs}")


def find_project_root_for_ignores(start_dir: Path, verbose: bool = False) -> Path:
    """
    Traverses upwards from start_dir to find a project root for ignore scanning.
    A project root is identified by a .git directory.
    If no .git directory is found up to the filesystem root, start_dir itself is returned.
    """
    current_path = start_dir.resolve()
    # Default to start_dir if no .git found. This is a conservative choice.
    project_root_candidate = current_path

    while True:
        if (current_path / ".git").is_dir():
            project_root_candidate = current_path
            if verbose:
                print(f"Found .git directory at: {project_root_candidate}. Using as ignore scan root.")
            break

        parent = current_path.parent
        if parent == current_path:  # Reached filesystem root
            if verbose:
                # If .git wasn't found, project_root_candidate remains start_dir.
                print(f"Reached filesystem root. No .git directory found above {start_dir}. "
                      f"Using {project_root_candidate} as ignore scan root.")
            break
        current_path = parent
    return project_root_candidate


def main():
    parser = argparse.ArgumentParser(
        description="Recursively scans a directory, reads file contents, and formats them for LLM analysis. "
                    "Obeys .gitignore and .llmignore rules. Output includes file paths as headers.",
        formatter_class=argparse.RawTextHelpFormatter  # Allows for better formatting of help text
    )
    parser.add_argument(
        "directory",
        type=str,
        nargs='?',  # Makes the argument optional
        default='.',  # Default to current directory if not provided
        help="The target directory to scan (e.g., /path/to/project).\n"
             "If not specified, defaults to the current working directory."
    )
    parser.add_argument(
        "output_file",
        type=str,
        nargs='?',  # Makes the argument optional
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

    # Resolve input directory to an absolute path for consistency
    input_dir_abs = Path(args.directory).resolve()

    # Determine the root directory for scanning ignore files
    # This can be different from input_dir_abs, especially if args.directory is relative.
    scan_root_for_ignores: Path
    original_input_path = Path(args.directory)

    if original_input_path.is_absolute():
        scan_root_for_ignores = input_dir_abs
        if args.verbose:
            print(f"Input path is absolute. Ignore patterns will be loaded from: {scan_root_for_ignores} downwards.")
    else:
        cwd = Path.cwd()
        scan_root_for_ignores = find_project_root_for_ignores(cwd, verbose=args.verbose)
        if args.verbose:
            print(f"Input path is relative. Current directory: {cwd}")
            print(f"Effective project root for ignores: {scan_root_for_ignores}")
            print(f"Actual content scan will be within: {input_dir_abs}")


    # Determine output file path. If not absolute, make it relative to current working directory.
    output_f = Path(args.output_file)
    if not output_f.is_absolute():
        output_f = Path.cwd() / output_f
    output_f = output_f.resolve()  # Ensure output path is absolute as well

    if not input_dir_abs.is_dir():
        print(
            f"Error: Input directory '{args.directory}' (resolved to '{input_dir_abs}') does not exist or is not a directory.")
        return

    print(f"Starting LLM Context Generator...")
    # The actual directory to be walked for content
    print(f"Target directory for content processing: {input_dir_abs}")
    # The root from which .gitignore/.llmignore files are searched and patterns made relative to
    print(f"Root for ignore pattern scanning: {scan_root_for_ignores}")

    # Warn if output file exists, as it will be overwritten.
    if output_f.exists():
        print(f"Warning: Output file '{output_f}' already exists. It will be overwritten.")

    print(f"Output will be saved to: {output_f}")
    if args.verbose:
        print("Verbose mode enabled.")

    # Load ignore patterns from .gitignore and .llmignore files
    # Patterns are loaded relative to scan_root_for_ignores
    ignore_spec = load_ignore_patterns(scan_root_for_ignores, verbose=args.verbose)

    # Process the directory and generate the output
    # Content is read from input_dir_abs
    # The spec is applied against paths relative to scan_root_for_ignores
    process_directory(input_dir_abs, output_f, ignore_spec, scan_root_for_ignores, verbose=args.verbose)


if __name__ == "__main__":
    main()
